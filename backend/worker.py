"""
ARQ Worker 入口
通过 `arq worker.worker` 或 `python -m backend.worker` 启动
"""
import asyncio
import logging
from arq.connections import RedisConnections, create_pool

from backend.config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [arq] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Redis 连接 URL
REDIS_URL = settings.model_dump().get("REDIS_URL") or "redis://localhost:6379/0"


async def startup(ctx: dict) -> None:
    """Worker 启动时初始化"""
    logger.info("ARQ Worker 启动中...")
    ctx["redis"] = await RedisConnections.from_url(REDIS_URL, create_pool=True)
    logger.info("Redis 连接成功")


async def shutdown(ctx: dict) -> None:
    """Worker 关闭时清理"""
    logger.info("ARQ Worker 关闭中...")
    pool: RedisConnections = ctx.get("redis")
    if pool:
        await pool.close()


class Worker:
    """ARQ Worker 配置"""

    functions = [
        "worker.generate_copywriting_job",
        "worker.search_trending_job",
    ]
    startup = startup
    shutdown = shutdown
    max_jobs = 4
    job_timeout = 300  # 5 分钟
    retry_jobs = True
    max_retry_count = 2


async def generate_copywriting_job(
    ctx: dict,
    user_id: int,
    request_data: dict,
    task_id: str,
) -> dict:
    """
    后台生成口播文案。

    Args:
        ctx: ARQ 上下文
        user_id: 用户 ID
        request_data: 文案生成请求的序列化数据（mode, topic, persona, ...）
        task_id: 任务 ID（用于状态查询）

    Returns:
        {"status": "completed", "task_id": ..., "data": {...}}
    """
    import json
    from datetime import datetime

    logger.info(f"[{task_id}] 开始生成文案: mode={request_data.get('mode')}")

    try:
        # 动态导入避免循环依赖
        from sqlalchemy.orm import Session
        from backend.config.database import SessionLocal
        from backend.services.copywriting_service import copywriting_service
        from backend.models.domain.persona import CopywritingGenerateRequest
        from backend.repository.task_repo import TaskRepository

        db = SessionLocal()
        task_repo = TaskRepository(db)
        task_repo.create(
            task_id=task_id,
            user_id=user_id,
            task_type="generate_copywriting",
            status="processing",
        )

        # 反序列化请求
        req = CopywritingGenerateRequest(**request_data)

        result = await copywriting_service.generate(req, db)

        task_repo.update(
            task_id=task_id,
            status="completed",
            result=result.model_dump(),
        )

        db.close()
        logger.info(f"[{task_id}] 文案生成完成")

        return {
            "status": "completed",
            "task_id": task_id,
            "data": result.model_dump(),
        }

    except Exception as e:
        logger.error(f"[{task_id}] 文案生成失败: {e}", exc_info=True)
        try:
            from backend.repository.task_repo import TaskRepository
            from backend.config.database import SessionLocal

            db = SessionLocal()
            task_repo = TaskRepository(db)
            task_repo.update(
                task_id=task_id,
                status="failed",
                error=str(e),
            )
            db.close()
        except Exception:
            pass

        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
        }


async def search_trending_job(
    ctx: dict,
    user_id: int,
    keyword: str,
    platforms: list[str],
    days: int,
    task_id: str,
) -> dict:
    """
    后台搜索热点话题。

    Args:
        ctx: ARQ 上下文
        user_id: 用户 ID
        keyword: 搜索关键词
        platforms: 平台列表
        days: 搜索天数
        task_id: 任务 ID

    Returns:
        {"status": "completed", "task_id": ..., "data": {...}}
    """
    logger.info(f"[{task_id}] 开始搜索热点: keyword={keyword}")

    try:
        from datetime import datetime
        from sqlalchemy.orm import Session
        from backend.config.database import SessionLocal
        from backend.services.trending_service import TrendingService
        from backend.repository.task_repo import TaskRepository

        db = SessionLocal()
        task_repo = TaskRepository(db)
        task_repo.create(
            task_id=task_id,
            user_id=user_id,
            task_type="search_trending",
            status="processing",
            metadata={"keyword": keyword, "platforms": platforms, "days": days},
        )

        trending_service = TrendingService()
        result = await trending_service.search(
            keyword=keyword,
            platforms=platforms,
            days=days,
        )

        task_repo.update(
            task_id=task_id,
            status="completed",
            result={
                "keyword": keyword,
                "total_count": len(result.hot_topics),
                "hot_topics": [t.model_dump() if hasattr(t, "model_dump") else t for t in result.hot_topics],
            },
        )

        db.close()
        logger.info(f"[{task_id}] 热点搜索完成: {len(result.hot_topics)} 条结果")

        return {
            "status": "completed",
            "task_id": task_id,
            "data": {
                "keyword": keyword,
                "total_count": len(result.hot_topics),
                "hot_topics": [t.model_dump() if hasattr(t, "model_dump") else t for t in result.hot_topics],
            },
        }

    except Exception as e:
        logger.error(f"[{task_id}] 热点搜索失败: {e}", exc_info=True)
        try:
            from backend.repository.task_repo import TaskRepository
            from backend.config.database import SessionLocal

            db = SessionLocal()
            task_repo = TaskRepository(db)
            task_repo.update(
                task_id=task_id,
                status="failed",
                error=str(e),
            )
            db.close()
        except Exception:
            pass

        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
        }
