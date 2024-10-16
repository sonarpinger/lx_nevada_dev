#!/usr/bin/env python3

import pyotp
import qrcode
import base64
from io import BytesIO
import database as db
from config import settings
from getpass import getpass
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError  

def auth_with_ldap(username, password):
    return_vals = {
        'authenticated': False,
        'user': None,
        'error': None
    }

    auth_user = None
    conn = None
    server = Server(settings.LDAP_SERVER, get_info=ALL)
    try:
        #authenticate with ldap server
        user = f"{username}@{settings.LDAP_DOMAIN}"
        conn = Connection(server, user=user, password=password, auto_bind=True)
        result = conn.result
        if result['description'] != 'success':
            return_vals['error'] = result['description']
        else:
            return_vals['authenticated'] = True
            return_vals['user'] = username
        
    except LDAPException as e:
        return_vals['error'] = e
    finally:
        if conn is not None:
            conn.unbind()
    return return_vals

def login_and_add_user(session, username, password):
    return_vals = auth_with_ldap(username, password)
    if return_vals['authenticated']:
        user = db.get_user_by_username(session, username)
        if user is None:
            print(f"User {username} not found in database, adding...")
            db.create_user(session, username)
            secret = generate_totp_secret()
            db.set_totp_secret(session, username, secret)
            uri = get_totp_qr_code(secret, username)
            print(f"QR Code URL: {uri}")
        else:
            print(f"User {username} already exists in database")

        session.commit()
        session.close()

def uri_to_base64_qr(uri):
    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert the image to a base64 string
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return img_base64

def generate_totp_secret():
    # Generate a random base32 secret key
    secret = pyotp.random_base32()
    print(f"Your secret key: {secret}")
    return secret

def get_totp_qr_code(secret, username):
    # Generate a QR code URL for Google Authenticator
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name="LX.NCR")
    print(f"QR Code URL for Google Authenticator: {uri}")
    return uri

def verify_totp(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

if __name__ == "__main__":
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    return_vals = auth_with_ldap(username, password)
    print(return_vals)