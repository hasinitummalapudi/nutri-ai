import json
import os
from pathlib import Path
from threading import Lock
from werkzeug.security import generate_password_hash, check_password_hash

USERS_PATH = Path(__file__).resolve().parent.parent / "users.json"
_LOCK = Lock()

def _load_users():
    if not USERS_PATH.exists():
        return {}
    try:
        return json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

def _save_users(users):
    tmp = USERS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(users, indent=2), encoding="utf-8")
    tmp.replace(USERS_PATH)

def create_user(email, password):
    email = email.strip().lower()
    if not email or "@" not in email or "." not in email.split("@", 1)[-1]:
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    with _LOCK:
        users = _load_users()
        if email in users:
            return False, "An account with this email already exists."
        users[email] = {"password": generate_password_hash(password)}
        _save_users(users)
    return True, "Account created successfully. You can now log in."

def authenticate(email, password):
    email = email.strip().lower()
    with _LOCK:
        user = _load_users().get(email)
    return bool(user and check_password_hash(user.get("password", ""), password))
