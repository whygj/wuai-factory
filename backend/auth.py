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
from database import get_db, DB_PATH
from models import User


def _load_or_create_secret() -> str:
    """优先环境变量；否则用 data/ 目录下的持久密钥文件（重启不掉线）。
    密钥文件与数据库同目录，data/ 已在 .gitignore，不会进仓库。"""
    env = os.environ.get("JWT_SECRET")
    if env:
        return env
    secret_file = os.path.join(os.path.dirname(DB_PATH), ".jwt_secret")
    try:
        if os.path.exists(secret_file):
            with open(secret_file, "r") as f:
                cached = f.read().strip()
                if cached:
                    return cached
        fresh = secrets.token_urlsafe(32)
        with open(secret_file, "w") as f:
            f.write(fresh)
        try:
            os.chmod(secret_file, 0o600)
        except OSError:
            pass
        return fresh
    except OSError:
        # 文件系统不可写时退化为随机值（保持原行为，重启会掉线）
        return secrets.token_urlsafe(32)


SECRET_KEY = _load_or_create_secret()
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
    # 停用/拒绝的账号即使 token 未过期也立即失效
    if user.status != "approved":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号已停用")
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
    "clerk": {"customer", "supplier", "purchase", "inbound", "production", "product", "sales", "shipment", "lab"},
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
