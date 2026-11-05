"""Database identities authenticated only by revocable browser sessions."""
from typing import Optional
from fastapi import Depends, HTTPException, Request
from passlib.context import CryptContext
from pydantic import BaseModel
from backend.app.database import users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = "patient"
    disabled: Optional[bool] = None
    doctor_id: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    hospital: Optional[str] = None


class UserInDB(User):
    hashed_password: str


def get_mongo_user(username):
    normalized = (username or '').strip().lower()
    if not normalized:
        return None
    return users_collection.find_one({'$or': [{'username': normalized}, {'email': normalized}]}, {'_id': 0})


def verify_password(plain_password, hashed_password):
    if len(plain_password.encode('utf-8')) > 72:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def get_password_hash(password):
    if len(password.encode('utf-8')) > 72:
        raise ValueError('Password must be at most 72 UTF-8 bytes.')
    return pwd_context.hash(password)


def authenticate_user(username, password):
    user = get_mongo_user(username)
    if not user or not user.get('hashed_password') or not verify_password(password, user['hashed_password']):
        return False
    return UserInDB(**user)


def get_current_user(request: Request) -> User:
    from backend.app.browser_sessions import resolve
    username = resolve(request)
    record = get_mongo_user(username) if username else None
    if not record:
        raise HTTPException(401, 'Sign in to continue.')
    return User(**record)


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(403, 'Inactive user')
    return current_user


def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != 'admin':
        raise HTTPException(403, 'Only administrators can perform this action.')
    return current_user
