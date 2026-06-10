from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import AssetHandoverLog, UploadResourceSystem
from app.schemas.handover import HandoverCreate, HandoverOut
from app.schemas.common import CommonResponse

router = APIRouter()


@router.get("/list")
def list_handovers(
    asset_type: str = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
):
    q = db.query(AssetHandoverLog)
    if asset_type:
        q = q.filter(AssetHandoverLog.asset_type == asset_type)
    total = q.count()
    items = q.order_by(AssetHandoverLog.operate_time.desc()).offset((page - 1) * size).limit(size).all()
    return CommonResponse(data={
        "total": total,
        "list": [HandoverOut.model_validate(i).model_dump() for i in items],
        "page": page,
        "size": size,
    })


@router.post("/create")
def create_handover(data: HandoverCreate, db: Session = Depends(get_db)):
    # Verify asset exists
    system = db.query(UploadResourceSystem).filter(UploadResourceSystem.sys_group_id == data.asset_id).first()
    if data.asset_type == "系统" and not system:
        raise HTTPException(status_code=404, detail="资产不存在")
    obj = AssetHandoverLog(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # Update maintainer if system
    if data.asset_type == "系统" and system:
        # In real scenario, update creator/maintainer field on system metadata
        pass
    return CommonResponse(data={"log_id": obj.log_id})
