import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.config import settings
from app.database import engine, Base
from app.routers import (
    dataset_metadata,
    dataset_catalog,
    meta_config,
    upload_group,
    upload_flow,
    audit,
    asset_handover,
    system_mgmt,
    auth,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表初始化完成")
    logger.info("定时任务: 系统状态每日更新已注册 (触发: POST /api/system/status/batch-update)")
    logger.info(f"服务启动完成: {settings.app_name} v1.0.0")
    yield


app = FastAPI(
    title=settings.app_name,
    description="夯实多模态数据管理能力 - 后端服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8001", "http://127.0.0.1:8001", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(dataset_metadata.router, prefix="/api/dataset", tags=["高质量数据集元数据"])
app.include_router(dataset_catalog.router, prefix="/api/catalog", tags=["数据集目录"])
app.include_router(meta_config.router, prefix="/api/meta-config", tags=["元模型配置"])
app.include_router(upload_group.router, prefix="/api/upload", tags=["集团上报"])
app.include_router(upload_flow.router, prefix="/api/upload", tags=["集团上报-新流程"])
app.include_router(audit.router, prefix="/api/audit", tags=["稽核规则"])
app.include_router(asset_handover.router, prefix="/api/handover", tags=["资产交接"])
app.include_router(system_mgmt.router, prefix="/api/system", tags=["系统管理"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.app_name}


# 挂载前端静态文件 - 放在所有 API 路由之后
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    logger.info(f"前端静态资源已挂载: {frontend_dist}")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # 非前端路由透传 404
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json", "health"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(str(frontend_dist / "index.html"))


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
