from sqlalchemy import and_
from .models import User, Environment, Base

def create_user(session, username):
  exists = session.query(User).filter(User.username == username).first()
  if exists:
    print(f"User {username} already exists")
    return get_user_by_username(session, username)
  u = User()
  u.username = username
  session.add(u)
  session.commit()

def create_environment_for_user(session, machine_name, course, vmid, username):
  #check if environment already exists for user
  user = get_user_by_username(session, username)
  criteria = and_(Environment.machine_name == machine_name, Environment.user_id == user.id, Environment.course == course, Environment.vmid == vmid)
  exists = session.query(Environment).filter(criteria).first()
  if exists:
    print(f"Environment {machine_name} already exists for user {user.username}")
    return
  print(f"Creating environment: {machine_name} for user: {user.username}")
  e = Environment()
  e.machine_name = machine_name
  e.course = course
  e.vmid = vmid
  user.environments.append(e)
  session.add(e)
  session.commit()

def get_totp_secret(session, username):
  user = get_user_by_username(session, username)
  session.refresh(user)
  return user.totp_secret

def set_totp_secret(session, username, secret):
  user = get_user_by_username(session, username)
  user.totp_secret = secret
  user.is_totp_enabled = True
  session.commit()

def add_ip_address(session, env, ip_address):
  environment = get_environment_by_machine_name(session, env)
  criteria = environment.ip_address is not None
  exists = session.query(Environment).filter(criteria).first()
  if exists:
    print(f"Environment already has an IP address set, changing from {exists.ip_address} to {ip_address}")
  environment.ip_address = ip_address
  session.commit()

def set_env_status(session, vmid, status):
  environment = get_environment_by_vmid(session, vmid)
  if environment is None:
    print(f"Environment with vmid {vmid} not found")
    return
  session.refresh(environment)
  environment.status = status
  print(f"Setting status for {environment.machine_name} to {status}")
  session.commit()

def get_env_status(session, env):
  environment = get_environment_by_machine_name(session, env)
  session.refresh(environment)
  return environment.status

def get_user_by_username(session, username):
  return session.query(User).filter(User.username == username).first()

def get_environment_by_machine_name(session, machine_name):
  return session.query(Environment).filter(Environment.machine_name == machine_name).first()

def get_environment_by_vmid(session, vmid):
  return session.query(Environment).filter(Environment.vmid == vmid).first()

def query_envs_for_user(session, user):
  session.refresh(user)
  user_id = user.id
  return session.query(Environment).filter(Environment.user_id == user.id).all()

def check_user_owns_vmid(session, username, vmid):
  user = get_user_by_username(session, username)
  criteria = and_(Environment.user_id == user.id, Environment.vmid == vmid)
  if session.query(Environment).filter(criteria).first():
    return True
  return False

def delete_user_and_envs(session, user):
  session.delete(user)
  session.commit()
  print(f"Deleted user: {user.username}")

def delete_env(session, env):
  environment = get_environment_by_machine_name(session, env)
  if environment is None:
    print(f"Environment {env} not found")
    return
  session.delete(environment)
  session.commit()

def get_all_users(session):
  return session.query(User).all()

def dump_user_to_dict(session, user):
  #refresh
  session.refresh(user)
  return {
    'username': user.username,
    'environments': [dump_env_to_dict(env) for env in user.environments]
  }

def query_all_envs(session):
  return session.query(Environment).all()

def dump_env_to_dict(env):
  return {
    'machine_name': env.machine_name,
    'course': env.course,
    'ip_address': env.ip_address,
    'status': env.status,
    'vmid': env.vmid
  }

def get_env_owner(session, env):
  environment = get_environment_by_machine_name(session, env)
  user = get_user_by_username(session, environment.user.username)
  return user.username