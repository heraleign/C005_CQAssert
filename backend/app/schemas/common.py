from typing import Optional, List, Any
from pydantic import BaseModel


class CommonResponse(BaseModel):
    code: str = "000000"
    message: str = "success"
    data: Any = None


class PageParam(BaseModel):
    page: int = 1
    size: int = 10


class PageResult(BaseModel):
    total: int
    list: List[dict]
    page: int
    size: int
