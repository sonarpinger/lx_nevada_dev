#!/usr/bin/env python3

import uvicorn
import logging
import datetime
from time import sleep
from config import settings
from typing import Annotated, Optional

import proxmox_api as prox
import database as db

from fastapi import FastAPI, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.endpoints import WebSocketEndpoint, WebSocket
from starlette.types import Receive, Scope, Send
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware

from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

from pydantic import BaseModel

class TokenData(BaseModel):
  preferred_username: str
  
def authenticate_token(request: Request):
  user = request.session.get('user', None)
  if user:
    return TokenData(preferred_username=user['preferred_username'])
  return None

#Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtain_session():
  try:
    session = db.get_session()
  except Exception as e:
    logger.error(f"Error obtaining session: {e}")
    raise
  return next(session)

app = FastAPI()

templates = Jinja2Templates(directory='templates')
app.mount('/static', StaticFiles(directory='static'), name='static')

### OIDC ###
origins = [
  "http://localhost:7000",
  "http://127.0.0.1:7000",
  "https://lx.nevada.dev",
  "http://lx.nevada.dev",
  "http://192.168.100.15",
]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.add_middleware(SessionMiddleware,
 secret_key=settings.OIDC_CLIENT_SECRET,
 max_age=None)

oauth: OAuth = OAuth()

def get_oauth() -> OAuth:
  yield oauth

oauth.register(
  name='keycloak',
  client_id=settings.OIDC_CLIENT_ID,
  client_secret=settings.OIDC_CLIENT_SECRET.get_secret_value(),
  server_metadata_url=settings.OIDC_METADATA_URL,
  client_kwargs={
      'scope': settings.OIDC_SCOPE,
  }
)

### ERROR ENDPOINTS ###

@app.exception_handler(404)
async def not_found(request: Request, exc: Exception):
  return templates.TemplateResponse("error404.html", {"request": request})

@app.exception_handler(500)
async def not_found(request: Request, exc: Exception):
  return templates.TemplateResponse("error500.html", {"request": request})

### OIDC ENDPOINTS ###

@app.get('/logout')
async def logout(request: Request) -> RedirectResponse:
  user = request.session.get('user', None)
  if user:
    id_token = user.get('id_token')
    goodbye_url = f'{settings.BASE_URL}/goodbye'
    request.session.pop('user', None)
    response = RedirectResponse(f'{settings.OIDC_LOGOUT_URL}?id_token_hint={id_token}&post_logout_redirect_uri={goodbye_url}')
    response.delete_cookie('mod_auth_openidc_session')
    response.delete_cookie('session')
    return response
  # return RedirectResponse(f'{settings.BASE_URL}/')

@app.get('/goodbye')
async def goodbye(request: Request):
  # return RedirectResponse(f'{settings.BASE_URL}/')
  return templates.TemplateResponse("goodbye.html", {"request": request})

@app.get('/login/')
async def login(request: Request, oauth_client: OAuth = Depends(get_oauth)):
  redirect_uri = f'{settings.BASE_URL}/auth/'
  return await oauth_client.keycloak.authorize_redirect(request, redirect_uri, kc_idp_hint='cilogon')

@app.get('/auth/', response_class=RedirectResponse)
async def auth(request: Request, oauth_client: OAuth = Depends(get_oauth)) -> RedirectResponse:
  try:
    token = await oauth_client.keycloak.authorize_access_token(request)
  except Exception as e:
    logger.error(f"Error obtaining token: {e}")
    response = RedirectResponse('/login')
    response.delete_cookie('mod_auth_openidc_session')
    response.delete_cookie('session')
    return response

  id_token = token.get('id_token')
  userinfo = token.get('userinfo')
  user = {
    'preferred_username': userinfo['preferred_username'],
    'id_token': id_token
  }
  request.session['user'] = user    
  return RedirectResponse('/')

### NORMAL ENDPOINTS ###

@app.get("/", response_class=HTMLResponse)
async def read_login(request: Request, session = Depends(obtain_session)):
  user = request.session.get('user', None)
  if user is not None:
    user = db.get_user_by_username(session, user['preferred_username'])
    no_data = user is None
    username = ""
    envs = []
    if not no_data:
      user_dict = db.dump_user_to_dict(session, user)
      username = user_dict['username']
      envs = user_dict['environments']
    return templates.TemplateResponse("student_index.html", {"request": request, "username": username, "envs": envs, "no_data": no_data})
  else:
    return RedirectResponse(url="/login", status_code=302)

@app.get("/{environment}/ttyd/")
async def ttyd(request: Request, environment: str, session = Depends(obtain_session)):
  user = request.session.get('user', None)
  if user is not None:
    user = db.get_user_by_username(session, user['preferred_username'])
    env = db.get_env_by_name(session, environment)
    if env is not None and db.check_user_owns_vmid(session, user.username, env.vmid):
      return JSONResponse
  return JSONResponse(content={"response": "Unauthorized"}, status_code=401)

@app.get("/api/refresh")
def refresh(request: Request, token: TokenData = Depends(authenticate_token), session = Depends(obtain_session)):
  if not token:
    user = request.session.get('user', None)
    if user:
      request.session.pop('user', None)
    return RedirectResponse(url="/login", status_code=302)
  username = token.preferred_username
  user = db.get_user_by_username(session, username)
  prox.refresh_status_for_user(user, session)
  return RedirectResponse(url="/", status_code=302)

@app.post("/api/{vmid}/start")
def start_vm(request: Request, vmid: int, token: TokenData = Depends(authenticate_token), session = Depends(obtain_session)):
  if not token:
      user = request.session.get('user', None)
      if user:
        request.session.pop('user', None)
      return RedirectResponse(url="/login", status_code=302)
  if db.check_user_owns_vmid(session, token.preferred_username, vmid):
    print(f"Starting VM {vmid}")
    response = prox.start(vmid, session)
    return JSONResponse(content={"response": response})

@app.post("/api/{vmid}/stop")
def stop_vm(request: Request, vmid: int, token: TokenData = Depends(authenticate_token), session = Depends(obtain_session)):
  if not token:
    user = request.session.get('user', None)
    if user:
      request.session.pop('user', None)
    return RedirectResponse(url="/login", status_code=302)
  if db.check_user_owns_vmid(session, token.preferred_username, vmid):
    print(f"Stopping VM {vmid}")
    response = prox.shutdown(vmid, session)
    return JSONResponse(content={"response": response})

if __name__ == '__main__':
  print("hi bingus!")
  uvicorn.run("main:app", host="127.0.0.1", port=7000, reload=True)
