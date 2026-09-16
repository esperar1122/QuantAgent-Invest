"""
TradingAgents-CN Worker Service
FastAPI-based worker application with health check and queue consumer
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.database import init_database, close_database
from app.core.redis_client import init_redis, close_redis
from app.worker.analysis_worker import AnalysisWorker

logger = logging.getLogger("worker_app")

worker_instance: Optional[AnalysisWorker] = None
worker_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Worker 应用生命周期管理"""
    global worker_instance, worker_task

    logger.info("🚀 启动 Worker 服务...")

    # 1. 尝试初始化数据库与 Redis 连接
    db_initialized = False
    redis_initialized = False
    try:
        await init_database()
        db_initialized = True
    except Exception as e:
        logger.warning(f"⚠️ 数据库初始化警告: {e}")

    try:
        await init_redis()
        redis_initialized = True
    except Exception as e:
        logger.warning(f"⚠️ Redis 初始化警告: {e}")

    # 2. 如果依赖就绪，启动 AnalysisWorker 队列监听任务
    if redis_initialized and db_initialized:
        try:
            worker_instance = AnalysisWorker()
            worker_task = asyncio.create_task(worker_instance.start())
            logger.info("✅ AnalysisWorker 已在后台启动，监听队列任务...")
        except Exception as e:
            logger.error(f"❌ AnalysisWorker 启动异常: {e}")
    else:
        logger.warning("⚠️ Redis/MongoDB 未完全连接，Worker 服务保持待机状态")

    yield

    # 3. 优雅停止
    logger.info("🛑 正在关闭 Worker 服务...")
    if worker_instance:
        worker_instance.running = False
    if worker_task and not worker_task.done():
        worker_task.cancel()
        try:
            await asyncio.wait_for(worker_task, timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    try:
        await close_database()
    except Exception:
        pass
    try:
        await close_redis()
    except Exception:
        pass
    logger.info("✅ Worker 服务已关闭")


app = FastAPI(
    title="TradingAgents Worker Service",
    description="异步分析任务 Worker 服务",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "service": "TradingAgents Worker",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查接口，供 start_dev.ps1 和监控系统探测"""
    is_running = bool(worker_instance and worker_instance.running)
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "TradingAgents Worker",
            "worker_id": worker_instance.worker_id if worker_instance else "standalone",
            "running": is_running,
            "has_task": bool(worker_instance and worker_instance.current_task)
        }
    )


@app.get("/status")
async def status():
    """获取当前 Worker 详细运行状态"""
    return {
        "worker_id": worker_instance.worker_id if worker_instance else None,
        "running": bool(worker_instance and worker_instance.running),
        "current_task": worker_instance.current_task if worker_instance else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.worker.worker_app:app", host="127.0.0.1", port=8001, log_level="info")
