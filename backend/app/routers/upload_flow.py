from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import CommonResponse
from app.schemas.upload import (
    SyncToMidRequest, AuditMidRequest, MidModifyRequest,
    SyncToResultRequest, UploadToGroupRequest, MidListQuery,
)
from app.upload_engine import UploadEngine

router = APIRouter()


def get_engine(db: Session = Depends(get_db)) -> UploadEngine:
    return UploadEngine(db, operator="管理员")


@router.post("/sync-to-mid")
def sync_to_mid(req: SyncToMidRequest, engine: UploadEngine = Depends(get_engine)):
    """同步本地元数据到中间表"""
    data = engine.sync_to_mid(
        asset_type=req.asset_type,
        scope_type=req.scope_type,
        scope_ids=req.scope_ids,
        overwrite_empty=req.overwrite_empty,
    )
    return CommonResponse(data=data)


@router.post("/audit")
def audit_mid(req: AuditMidRequest, engine: UploadEngine = Depends(get_engine)):
    """对中间表执行稽核"""
    data = engine.audit_mid(
        asset_type=req.asset_type,
        scope_type=req.scope_type,
        scope_ids=req.scope_ids,
    )
    return CommonResponse(data=data)


@router.get("/mid-list")
def mid_list(
    asset_type: str = Query(),
    sys_code: Optional[str] = None,
    sys_name: Optional[str] = None,
    record_name: Optional[str] = None,
    audit_status: Optional[str] = None,
    upload_status: Optional[str] = None,
    sys_status: Optional[str] = None,
    sys_func_type: Optional[str] = None,
    if_managed: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询中间表数据"""
    engine = UploadEngine(db)
    filters = {}
    for k, v in [("sys_code", sys_code), ("sys_name", sys_name),
                 ("record_name", record_name), ("audit_status", audit_status),
                 ("upload_status", upload_status), ("status", sys_status),
                 ("sys_func_type", sys_func_type), ("if_managed", if_managed)]:
        if v:
            filters[k] = v

    data = engine.query_mid_list(asset_type, filters, page, size)
    return CommonResponse(data=data)


@router.put("/mid-modify")
def mid_modify(req: MidModifyRequest, engine: UploadEngine = Depends(get_engine)):
    """修改中间表字段"""
    data = engine.modify_mid(
        asset_type=req.asset_type,
        local_biz_id=req.local_biz_id,
        modify_fields=req.modify_fields,
        modify_reason=req.modify_reason,
    )
    return CommonResponse(data=data)


@router.post("/sync-to-result")
def sync_to_result(req: SyncToResultRequest, engine: UploadEngine = Depends(get_engine)):
    """同步合规记录到结果表"""
    data = engine.sync_to_result(
        asset_type=req.asset_type,
        scope_type=req.scope_type,
        scope_ids=req.scope_ids,
    )
    return CommonResponse(data=data)


@router.post("/upload-to-group")
def upload_to_group(req: UploadToGroupRequest, engine: UploadEngine = Depends(get_engine)):
    """上传集团"""
    data = engine.upload_to_group(
        asset_type=req.asset_type,
        scope_type=req.scope_type,
        scope_ids=req.scope_ids,
        upload_mode=req.upload_mode,
    )
    return CommonResponse(data=data)


@router.get("/modify-log")
def modify_log(
    asset_type: Optional[str] = None,
    local_biz_id: Optional[str] = None,
    operator: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    field_name: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询修改日志"""
    engine = UploadEngine(db)
    data = engine.query_modify_log(
        asset_type=asset_type, local_biz_id=local_biz_id,
        operator=operator, start_time=start_time, end_time=end_time,
        field_name=field_name, page=page, size=size,
    )
    return CommonResponse(data=data)


@router.get("/upload-log")
def upload_log(
    asset_type: Optional[str] = None,
    batch_no: Optional[str] = None,
    operator: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    upload_status: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询上传日志"""
    engine = UploadEngine(db)
    data = engine.query_upload_log(
        asset_type=asset_type, batch_no=batch_no,
        operator=operator, start_time=start_time, end_time=end_time,
        upload_status=upload_status, page=page, size=size,
    )
    return CommonResponse(data=data)
