"""
任务队列路由
通过 ARQ 将耗时操作（文案生成、热点搜索）提交到 Redis 队列异步执行
"""
import logging
import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List

from arq.connections import RedisSettings, create_pool

from backend.config.database import get_db
from backend.config.settings import settings
from backend.models.database.tables import UserTable
from backend.api.dependencies import get_current_user
from backend.services.auth_service_typed import auth_service
from backend.utils.api_response import success_response, error_response, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["任务队列"])


# ------------------- Redis 连接 -------------------

def _parse_redis_url(url: str) -> dict:
    """将 redis:// URL 解析为 RedisSettings 参数"""
    import re
    m = re.match(r'redis://(?:::?)(?:(\w+):(\w+)@)?([^:]+)(?::(\d+))?(?:/(\d+))?', url)
    if not m:
        return {}
    return {
        "host": m.group(3),
        "port": int(m.group(4) or "6379"),
        "database": int(m.group(5) or "0"),
    }


async def get_redis_pool():
    """获取 ARQ Redis 连接池（依赖注入）"""
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    kwargs = _parse_redis_url(redis_url)
    pool = await create_pool(RedisSettings(**kwargs))
    return pool


# ------------------- 请求模型 -------------------

class TaskSubmitRequest(BaseModel):
    """提交异步任务请求"""
    task_type: str = Field(..., description="任务类型: generate_copywriting | search_trending")
    params: dict = Field(..., description="任务参数（与同步 API 请求体一致）")


class TaskResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str  # pending | processing | completed | failed
    task_type: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: Optional[str] = None


# ------------------- 路由 -------------------

@router.post("/submit")
async def submit_task(
    request: TaskSubmitRequest,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    提交异步任务到队列。

    立即返回 task_id，前端通过 GET /tasks/{task_id} 轮询状态。

    支持的 task_type:
    - generate_copywriting: params 需包含 mode, persona, 以及 topic/hotspot_content/original_text
    - search_trending: params 需包含 keyword, platforms, days
    """
    # 配额检查 + 预扣
    quota_ops = {
        "generate_copywriting": "generate_copywriting",
        "search_trending": "search_trending",
    }
    op = quota_ops.get(request.task_type)
    if op:
        ok, balance = auth_service.check_quota(db, current_user.id, op)
        if not ok:
            return error_response(
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message=f"配额不足，当前余额: {balance}",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        deducted, _ = auth_service.deduct_quota(db, current_user.id, op)
        if not deducted:
            return error_response(
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message=f"配额不足，当前余额: {current_user.quota_balance}",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    task_id = str(uuid.uuid4())

    try:
        from backend.main import get_arq_pool
        arq_pool = await get_arq_pool()
        if arq_pool is None:
            if op:
                auth_service.refund_quota(db, current_user.id, op)
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="任务队列未就绪（Redis 未连接）",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        job_meta = {
            "task_id": task_id,
            "task_type": request.task_type,
            "user_id": current_user.id,
        }

        if request.task_type == "generate_copywriting":
            await arq_pool.enqueue_job(
                "generate_copywriting_job",
                user_id=current_user.id,
                request_data=request.params,
                task_id=task_id,
                _job_id=task_id,
            )
        elif request.task_type == "search_trending":
            platforms = request.params.get("platforms", ["douyin", "weibo", "xiaohongshu"])
            await arq_pool.enqueue_job(
                "search_trending_job",
                user_id=current_user.id,
                keyword=request.params.get("keyword", ""),
                platforms=platforms,
                days=request.params.get("days", 7),
                task_id=task_id,
                _job_id=task_id,
            )
        else:
            if op:
                auth_service.refund_quota(db, current_user.id, op)
            return error_response(
                code=ErrorCode.INVALID_INPUT,
                message=f"不支持的任务类型: {request.task_type}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"任务已提交: {task_id} ({request.task_type})")

        return success_response(
            data={"task_id": task_id, "status": "pending"},
            message="任务已提交，请稍后查询结果",
        )

    except Exception as e:
        err_msg = str(e).lower()
        # Redis 连接失效（startup 后 Redis 中途挂掉的场景）
        # 触发重置 pool，下次请求会走 lazy 重连路径
        is_redis_err = any(kw in err_msg for kw in ["timeout", "connection", "redis"])
        if is_redis_err:
            try:
                import backend.main as main_mod
                main_mod.arq_pool = None
                logger.warning(f"检测到 Redis 连接失效，已重置 arq_pool 等待重连: {e}")
            except Exception:
                pass

        logger.error(f"提交任务失败: {e}")
        if op:
            try:
                auth_service.refund_quota(db, current_user.id, op)
            except Exception as refund_err:
                logger.error(f"退还配额也失败了: {refund_err}")
        if is_redis_err:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="任务队列暂不可用，请稍后重试",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"提交任务失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
):
    """
    查询任务状态。

    返回:
    - pending: 排队中
    - processing: 处理中
    - completed: 已完成（result 包含数据）
    - failed: 失败（error 包含原因）
    """
    try:
        from backend.main import get_arq_pool
        arq_pool = await get_arq_pool()
        if arq_pool is None:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="任务队列未就绪",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        from arq.jobs import Job, JobStatus

        job = Job(task_id, redis=arq_pool)
        js = await job.status()

        # ARQ JobStatus → 对外状态
        status_map = {
            JobStatus.deferred: "pending",
            JobStatus.queued: "pending",
            JobStatus.in_progress: "processing",
            JobStatus.complete: "completed",
            JobStatus.not_found: None,  # 任务不存在
        }
        current_status = status_map.get(js)

        if current_status is None:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="任务不存在",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        response_data = {
            "task_id": task_id,
            "status": current_status,
        }

        # 仅在终态时取 result_info(成功/失败)
        if current_status == "completed":
            info = await job.result_info()
            if info is not None:
                if info.success:
                    result = info.result
                    if isinstance(result, dict):
                        # worker 返回 {"status":..., "data":...} 或 {"status":"failed",...}
                        if result.get("status") == "failed":
                            response_data["status"] = "failed"
                            response_data["error"] = result.get("error")
                        else:
                            response_data["data"] = result.get("data", result)
                    else:
                        response_data["data"] = result
                else:
                    # worker 抛了异常
                    response_data["status"] = "failed"
                    response_data["error"] = str(info.result) if info.result else "任务执行异常"

        return success_response(data=response_data, message="获取任务状态成功")

    except Exception as e:
        logger.error(f"查询任务状态失败: {e}", exc_info=True)
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"查询任务状态失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/history")
async def get_task_history(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
):
    """
    获取当前用户的任务历史（从数据库查询）。
    """
    try:
        from backend.repository.task_repo import TaskRepository
        repo = TaskRepository(db)
        tasks = (
            db.query(UserTable)
            .filter(UserTable.id == current_user.id)
            .first()
        )
        if not tasks:
            return success_response(data={"tasks": [], "total": 0}, message="暂无任务历史")

        # 查询该用户的任务
        from backend.models.database.tables import TaskTable
        total = db.query(TaskTable).filter(TaskTable.user_id == current_user.id).count()
        task_list = (
            db.query(TaskTable)
            .filter(TaskTable.user_id == current_user.id)
            .order_by(TaskTable.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return success_response(
            data={
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "status": t.status,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                    }
                    for t in task_list
                ],
                "total": total,
                "page": page,
                "size": size,
            },
            message="获取任务历史成功",
        )
    except Exception as e:
        logger.error(f"获取任务历史失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取任务历史失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
