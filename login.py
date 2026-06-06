import json
import hashlib
import os
import uuid
from datetime import datetime

USERS_FILE = 'users.json'

def init_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    init_users_file()
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    if username not in users:
        return {'status': 'error', 'error': 'User not found'}
    
    if users[username]['password'] == hash_password(password):
        token = str(uuid.uuid4())
        users[username]['last_login'] = datetime.now().isoformat()
        users[username]['token'] = token
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
        return {'status': 'ok', 'token': token, 'username': username}
    
    return {'status': 'error', 'error': 'Invalid password'}