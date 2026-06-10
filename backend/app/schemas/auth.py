from typing import Optional
from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    user_id: int
    username: str
    real_name: str
    org_unit: Optional[str]
    org_dept: Optional[str]
    roles: list = []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None
