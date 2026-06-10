from typing import Optional, Any
from pydantic import BaseModel


class CatalogCreate(BaseModel):
    catalog_id: str
    catalog_name: str
    parent_id: Optional[str] = None
    catalog_level: int
    catalog_type: Optional[str] = None
    sort_order: int = 0


class CatalogUpdate(BaseModel):
    catalog_name: Optional[str] = None
    parent_id: Optional[str] = None
    catalog_level: Optional[int] = None
    catalog_type: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class CatalogOut(BaseModel):
    catalog_id: str
    catalog_name: str
    parent_id: Optional[str]
    catalog_level: int
    catalog_type: Optional[str]
    sort_order: int
    status: str
    create_time: Any

    class Config:
        from_attributes = True
