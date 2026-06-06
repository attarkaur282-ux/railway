import json
import hashlib
import os
from datetime import datetime

USERS_FILE = 'users.json'

def init_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_account(username, email, password):
    init_users_file()
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    if username in users:
        return {'status': 'error', 'error': 'Username already exists'}
    
    if len(password) < 6:
        return {'status': 'error', 'error': 'Password must be at least 6 characters'}
    
    users[username] = {
        'email': email,
        'password': hash_password(password),
        'created_at': datetime.now().isoformat(),
        'last_login': None,
        'token': None,
        'coins': 5000,
        'level': 1
    }
    
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)
    
    return {'status': 'ok', 'message': 'Account created successfully'}