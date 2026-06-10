from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import UploadResourceSystem
from app.schemas.common import CommonResponse

router = APIRouter()


@router.get("/status/list")
def list_system_status(
    sys_name: Optional[str] = None,
    sys_code: Optional[str] = None,
    record_name: Optional[str] = None,
    org_unit: Optional[str] = None,
    status: Optional[str] = None,
    is_compliant: Optional[str] = None,
    is_uploaded: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """系统状态查询（增强：新增定级备案名称、维护单位、是否合规筛选）"""
    q = db.query(UploadResourceSystem)
    if sys_name:
        q = q.filter(UploadResourceSystem.sys_name.like(f"%{sys_name}%"))
    if sys_code:
        q = q.filter(UploadResourceSystem.sys_code.like(f"%{sys_code}%"))
    if record_name:
        q = q.filter(UploadResourceSystem.record_name.like(f"%{record_name}%"))
    if org_unit:
        q = q.filter(UploadResourceSystem.org_unit == org_unit)
    if status:
        q = q.filter(UploadResourceSystem.status == status)
    if is_compliant:
        q = q.filter(UploadResourceSystem.is_compliant == is_compliant)
    if is_uploaded:
        q = q.filter(UploadResourceSystem.is_uploaded == is_uploaded)
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    rows = []
    for i in items:
        rows.append({
            "id": i.id,
            "sys_group_id": i.sys_group_id,
            "sys_code": i.sys_code,
            "sys_name": i.sys_name,
            "record_name": i.record_name,
            "org_unit": i.org_unit,
            "org_dept": i.org_dept,
            "biz_owner": i.biz_owner,
            "status": i.status,
            "online_time": i.online_time,
            "is_compliant": i.is_compliant,
            "non_compliant_reason": i.non_compliant_reason,
            "is_uploaded": i.is_uploaded,
            "master_data_code": i.master_data_code,
        })
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.post("/status/batch-update")
def batch_update_status(db: Session = Depends(get_db)):
    """定时任务：每日凌晨更新系统状态（模块五 5.1）"""
    items = db.query(UploadResourceSystem).all()
    now = datetime.now()
    updated = 0
    for item in items:
        if not item.online_time:
            continue
        try:
            online = datetime.strptime(item.online_time, "%Y%m%d")
            if online < now:
                item.status = "建设中"
            else:
                item.status = "在用"
            updated += 1
        except Exception:
            continue
    db.commit()
    return CommonResponse(data={"updated": updated})


@router.post("/master-data/sync")
def sync_master_data(sys_group_id: str, master_data_code: str, db: Session = Depends(get_db)):
    """集团主数据编码同步（模块五 5.3）"""
    obj = db.query(UploadResourceSystem).filter(UploadResourceSystem.sys_group_id == sys_group_id).first()
    if not obj:
        return CommonResponse(code="400001", message="系统不存在")
    old_code = obj.master_data_code
    obj.master_data_code = master_data_code
    obj.oper_type = "1"
    obj.oper_time = datetime.now().strftime("%Y%m%d%H%M%S")
    db.commit()
    return CommonResponse(data={
        "sys_group_id": sys_group_id,
        "old_code": old_code,
        "new_code": master_data_code,
    })


@router.get("/master-data/query")
def query_master_data(sys_group_id: str, db: Session = Depends(get_db)):
    """查询集团主数据编码"""
    obj = db.query(UploadResourceSystem).filter(UploadResourceSystem.sys_group_id == sys_group_id).first()
    if not obj:
        return CommonResponse(code="400001", message="系统不存在")
    return CommonResponse(data={
        "sys_group_id": obj.sys_group_id,
        "master_data_code": obj.master_data_code,
        "status": obj.status,
    })
