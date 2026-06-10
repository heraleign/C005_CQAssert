from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.dataset import DatasetCatalog
from app.schemas.catalog import CatalogCreate, CatalogUpdate, CatalogOut
from app.schemas.common import CommonResponse

router = APIRouter()


@router.get("/tree")
def get_catalog_tree(db: Session = Depends(get_db)):
    items = db.query(DatasetCatalog).filter(DatasetCatalog.status == "1").order_by(DatasetCatalog.sort_order).all()
    nodes = {}
    root = []
    for i in items:
        node = {
            "catalog_id": i.catalog_id,
            "catalog_name": i.catalog_name,
            "parent_id": i.parent_id,
            "catalog_level": i.catalog_level,
            "catalog_type": i.catalog_type,
            "sort_order": i.sort_order,
            "children": [],
        }
        nodes[i.catalog_id] = node
    for i in items:
        node = nodes[i.catalog_id]
        if i.parent_id and i.parent_id in nodes:
            nodes[i.parent_id]["children"].append(node)
        else:
            root.append(node)
    return CommonResponse(data=root)


@router.post("/create")
def create_catalog(data: CatalogCreate, db: Session = Depends(get_db)):
    if db.query(DatasetCatalog).filter(DatasetCatalog.catalog_id == data.catalog_id).first():
        raise HTTPException(status_code=400, detail="目录ID已存在")
    obj = DatasetCatalog(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return CommonResponse(data={"catalog_id": obj.catalog_id})


@router.post("/update/{catalog_id}")
def update_catalog(catalog_id: str, data: CatalogUpdate, db: Session = Depends(get_db)):
    obj = db.query(DatasetCatalog).filter(DatasetCatalog.catalog_id == catalog_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="目录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return CommonResponse()


@router.post("/delete/{catalog_id}")
def delete_catalog(catalog_id: str, db: Session = Depends(get_db)):
    obj = db.query(DatasetCatalog).filter(DatasetCatalog.catalog_id == catalog_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="目录不存在")
    obj.status = "0"
    db.commit()
    return CommonResponse()
