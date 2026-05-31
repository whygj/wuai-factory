import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db
from models import User

SECRET_KEY = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def _extract_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(default=None),
) -> str:
    if credentials:
        return credentials.credentials
    if access_token:
        return access_token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def get_current_user(
    token: str = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> User:
    return _decode_token(token, db)


def get_current_role(
    current_user: User = Depends(get_current_user),
    token: str = Depends(_extract_token),
) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role: str = payload.get("current_role")
        if role is None:
            roles = json.loads(current_user.roles)
            return roles[0] if roles else "clerk"
        return role
    except JWTError:
        roles = json.loads(current_user.roles)
        return roles[0] if roles else "clerk"


WRITE_PERMISSIONS = {
    "boss": set(),
    "clerk": {"customer", "supplier", "purchase", "inbound", "production", "sales", "shipment", "lab"},
    "leader": {"production", "lab"},
}

ROLE_LABELS = {
    "boss": "老板",
    "clerk": "内勤",
    "leader": "班长",
}


def check_write_permission(current_role: str, module: str):
    if current_role == "boss":
        return True
    allowed = WRITE_PERMISSIONS.get(current_role, set())
    return module in allowed
