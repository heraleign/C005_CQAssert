from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database import get_db
from app.models.dataset import DatasetMetadata, DatasetQuality, UploadMultimodalDataset
from app.schemas.dataset import DatasetMetadataCreate, DatasetMetadataUpdate, DatasetMetadataOut, DatasetQuery, DatasetQualitySchema
from app.schemas.common import CommonResponse, PageResult

router = APIRouter()


@router.post("/list")
def list_datasets(query: DatasetQuery, db: Session = Depends(get_db)):
    q = db.query(DatasetMetadata)
    if query.dataset_name:
        q = q.filter(DatasetMetadata.dataset_name.like(f"%{query.dataset_name}%"))
    if query.dataset_type:
        q = q.filter(DatasetMetadata.dataset_type == query.dataset_type)
    if query.org_unit:
        q = q.filter(DatasetMetadata.org_unit == query.org_unit)
    if query.org_dept:
        q = q.filter(DatasetMetadata.org_dept == query.org_dept)
    if query.biz_scene:
        q = q.filter(DatasetMetadata.biz_scene == query.biz_scene)
    if query.biz_sub_scene:
        q = q.filter(DatasetMetadata.biz_sub_scene == query.biz_sub_scene)
    if query.is_in_lake:
        q = q.filter(DatasetMetadata.is_in_lake == query.is_in_lake)
    if query.status:
        q = q.filter(DatasetMetadata.status == query.status)
    if query.is_compliant:
        q = q.filter(DatasetMetadata.is_compliant == query.is_compliant)

    total = q.count()
    items = q.offset((query.page - 1) * query.size).limit(query.size).all()

    return CommonResponse(data={
        "total": total,
        "list": [DatasetMetadataOut.model_validate(i).model_dump() for i in items],
        "page": query.page,
        "size": query.size,
    })


@router.get("/detail/{dataset_id}")
def get_dataset_detail(dataset_id: str, db: Session = Depends(get_db)):
    item = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == dataset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return CommonResponse(data=DatasetMetadataOut.model_validate(item).model_dump())


@router.post("/create")
def create_dataset(data: DatasetMetadataCreate, db: Session = Depends(get_db)):
    if db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == data.dataset_id).first():
        raise HTTPException(status_code=400, detail="数据集唯一标识已存在")
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    obj = DatasetMetadata(
        **data.model_dump(),
        oper_type="0",
        oper_time=now,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return CommonResponse(data={"dataset_id": obj.dataset_id})


@router.post("/update/{dataset_id}")
def update_dataset(dataset_id: str, data: DatasetMetadataUpdate, db: Session = Depends(get_db)):
    obj = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == dataset_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="数据集不存在")
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(obj, k, v)
    obj.oper_type = "1"
    obj.oper_time = now
    db.commit()
    db.refresh(obj)
    return CommonResponse(data={"dataset_id": obj.dataset_id})


@router.post("/delete/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    obj = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == dataset_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="数据集不存在")
    db.delete(obj)
    db.commit()
    return CommonResponse()


@router.post("/quality/add/{dataset_id}")
def add_quality(dataset_id: str, data: DatasetQualitySchema, db: Session = Depends(get_db)):
    obj = DatasetQuality(dataset_id=dataset_id, **data.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return CommonResponse(data={"quality_id": obj.quality_id})


@router.get("/quality/list/{dataset_id}")
def list_quality(dataset_id: str, db: Session = Depends(get_db)):
    items = db.query(DatasetQuality).filter(DatasetQuality.dataset_id == dataset_id).all()
    return CommonResponse(data=[DatasetQualitySchema.model_validate(i).model_dump() for i in items])
