from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import CommonResponse
from app.schemas.upload import (
    SyncToMidRequest, AuditMidRequest, MidModifyRequest,
    SyncToResultRequest, UploadToGroupRequest, MidListQuery,
    SyncToResultMidRequest, ConfirmUploadRequest,
    MarkExcludeRequest, MergeRecordsRequest,
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
        sync_type=req.sync_type,
    )
    return CommonResponse(data=data)


@router.post("/audit")
def audit_mid(req: AuditMidRequest, engine: UploadEngine = Depends(get_engine)):
    """对中间表执行稽核（支持级联稽核）"""
    data = engine.audit_mid(
        asset_type=req.asset_type,
        scope_type=req.scope_type,
        scope_ids=req.scope_ids,
        cascade=req.cascade,
    )
    return CommonResponse(data=data)


@router.get("/mid-options")
def mid_options(
    asset_type: str = Query(),
    parent_local_biz_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取级联选择框选项（按层级+父级过滤）"""
    engine = UploadEngine(db)
    data = engine.query_mid_options(asset_type, parent_local_biz_id)
    return CommonResponse(data=data)


@router.get("/mid-list")
def mid_list(
    asset_type: str = Query(),
    parent_local_biz_id: Optional[str] = None,
    parent_level: Optional[str] = None,
    sys_code: Optional[str] = None,
    sys_name: Optional[str] = None,
    record_name: Optional[str] = None,
    audit_status: Optional[str] = None,
    upload_status: Optional[str] = None,
    sys_status: Optional[str] = None,
    sys_func_type: Optional[str] = None,
    if_managed: Optional[str] = None,
    upload_flag: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询中间表数据（支持按父级 local_biz_id 过滤，支持间接上级联过滤）"""
    engine = UploadEngine(db)
    filters = {}
    if parent_local_biz_id:
        filters["parent_local_biz_id"] = parent_local_biz_id
    if parent_level:
        filters["parent_level"] = parent_level
    for k, v in [("sys_code", sys_code), ("sys_name", sys_name),
                 ("record_name", record_name), ("audit_status", audit_status),
                 ("upload_status", upload_status), ("status", sys_status),
                 ("sys_func_type", sys_func_type), ("if_managed", if_managed),
                 ("upload_flag", upload_flag)]:
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


# ─── 新增：三层流程 endpoints ─────────────────

@router.post("/sync-to-result-mid")
def sync_to_result_mid(req: SyncToResultMidRequest, engine: UploadEngine = Depends(get_engine)):
    """同步合规记录到中间结果表（带账期）"""
    data = engine.sync_to_result_mid(
        asset_type=req.asset_type,
        scope_type=req.scope_type,
        scope_ids=req.scope_ids,
        bill_month=req.bill_month,
    )
    return CommonResponse(data=data)


@router.post("/confirm-upload")
def confirm_upload(req: ConfirmUploadRequest, engine: UploadEngine = Depends(get_engine)):
    """确认上传到集团结果表"""
    data = engine.confirm_upload(
        asset_type=req.asset_type,
        scope_type=req.scope_type,
        scope_ids=req.scope_ids,
        bill_month=req.bill_month,
    )
    return CommonResponse(data=data)


@router.post("/mark-exclude")
def mark_exclude(req: MarkExcludeRequest, engine: UploadEngine = Depends(get_engine)):
    """标记中间表记录不上传/恢复上传"""
    data = engine.mark_upload_flag(
        asset_type=req.asset_type,
        asset_id=req.asset_id,
        exclude_flag=req.exclude_flag,
        reason=req.reason,
    )
    return CommonResponse(data=data)


@router.post("/merge-records")
def merge_records(req: MergeRecordsRequest, engine: UploadEngine = Depends(get_engine)):
    """合并定级备案名称重复的记录"""
    data = engine.merge_records(
        asset_type=req.asset_type,
        source_ids=req.source_ids,
        target_id=req.target_id,
        bill_month=req.bill_month,
    )
    return CommonResponse(data=data)


# ─── 新增：查询 endpoints ─────────────────────

@router.get("/result-mid-list")
def result_mid_list(
    asset_type: Optional[str] = None,
    bill_month: Optional[str] = None,
    result_status: Optional[str] = None,
    group_unique_id: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询中间结果表（带账期）"""
    engine = UploadEngine(db)
    data = engine.query_result_mid_list(
        asset_type=asset_type, bill_month=bill_month,
        result_status=result_status, group_unique_id=group_unique_id,
        page=page, size=size,
    )
    return CommonResponse(data=data)


@router.get("/group-result-list")
def group_result_list(
    asset_type: Optional[str] = None,
    group_unique_id: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询集团结果表（全量只读）"""
    engine = UploadEngine(db)
    data = engine.query_group_result_list(
        asset_type=asset_type, group_unique_id=group_unique_id,
        page=page, size=size,
    )
    return CommonResponse(data=data)


@router.get("/exclude-marks")
def exclude_marks(
    sys_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询排除上传标记"""
    engine = UploadEngine(db)
    data = engine.query_exclude_marks(
        sys_id=sys_id, asset_type=asset_type, page=page, size=size,
    )
    return CommonResponse(data=data)


@router.get("/merge-logs")
def merge_logs(
    asset_type: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询合并日志"""
    engine = UploadEngine(db)
    data = engine.query_merge_logs(asset_type=asset_type, page=page, size=size)
    return CommonResponse(data=data)


@router.get("/pending-merges")
def pending_merges(
    bill_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """查询待合并建议"""
    engine = UploadEngine(db)
    data = engine.query_pending_merges(bill_month=bill_month)
    return CommonResponse(data=data)


@router.get("/bill-months")
def bill_months():
    """获取当前账期"""
    current = UploadEngine._calc_bill_month()
    return CommonResponse(data={"current": current})


# ─── 原有 endpoints ────────────────────────────

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


@router.get("/result-list")
def result_list(
    asset_type: Optional[str] = None,
    upload_status: Optional[str] = None,
    batch_no: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """查询上传结果表（最终上传数据确认查看）"""
    engine = UploadEngine(db)
    data = engine.query_result_list(
        asset_type=asset_type, upload_status=upload_status,
        batch_no=batch_no, page=page, size=size,
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
