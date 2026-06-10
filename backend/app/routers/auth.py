from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.auth import UserLogin, Token, UserOut
from app.schemas.common import CommonResponse

router = APIRouter()


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


@router.post("/login", response_model=CommonResponse)
def login(data: UserLogin):
    # Simplified: in production, verify against user table with hashed password
    if data.username == "admin" and data.password == "admin123":
        token = create_access_token({"sub": data.username, "role": "admin"})
        return CommonResponse(data=Token(
            access_token=token,
            user={"user_id": 1, "username": "admin", "real_name": "系统管理员", "roles": ["admin"]},
        ).model_dump())
    if data.username == "user" and data.password == "user123":
        token = create_access_token({"sub": data.username, "role": "user"})
        return CommonResponse(data=Token(
            access_token=token,
            user={"user_id": 2, "username": "user", "real_name": "普通用户", "roles": ["user"]},
        ).model_dump())
    raise HTTPException(status_code=401, detail="用户名或密码错误")


@router.get("/me")
def get_current_user():
    return CommonResponse(data={"user_id": 1, "username": "admin", "real_name": "系统管理员", "roles": ["admin"]})
