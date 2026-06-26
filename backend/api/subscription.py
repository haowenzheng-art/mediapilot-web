"""
话题订阅路由
使用统一的 API 响应模型
"""
import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.domain.subscription import (
    SubscriptionCreate, SubscriptionUpdate,
    SubscriptionResponse, PushRecordResponse
)
from backend.models.schemas.api_response import ErrorCode
from backend.utils.api_response import (
    success_response,
    error_response,
)
from backend.services.subscription_service import subscription_service
from backend.models.database.tables import UserTable
from backend.api.dependencies import get_current_user
from backend.services.auth_service_typed import auth_service

router = APIRouter(prefix="/subscriptions", tags=["话题订阅"])


def _map_value_error(e: ValueError):
    """把服务层 ValueError 按 message 文案映射到合适的状态码"""
    msg = str(e)
    if "不存在" in msg:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND
        )
    if "无权" in msg:
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message=msg,
            status_code=status.HTTP_403_FORBIDDEN
        )
    return error_response(
        code=ErrorCode.INVALID_INPUT,
        message=msg,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@router.get("")
async def get_subscriptions(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    获取用户的话题订阅列表
    """
    try:
        subscriptions = subscription_service.get_user_subscriptions(db, current_user.id)
        return success_response(
            data={"subscriptions": subscriptions},
            message="获取订阅列表成功"
        )
    except Exception as e:
        logger.error(f"获取订阅列表失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取订阅列表失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("")
async def create_subscription(
    sub_in: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    创建话题订阅

    与 copywriting 保持一致的配额模式：先校验 → 创建 → 创建失败回滚配额。
    """
    ok, balance = auth_service.check_quota(db, current_user.id, "create_subscription")
    if not ok:
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    deducted, _ = auth_service.deduct_quota(db, current_user.id, "create_subscription")
    if not deducted:
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {current_user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        subscription = subscription_service.create_subscription(db, current_user.id, sub_in)
        return success_response(
            data={"subscription": subscription},
            message="创建订阅成功"
        )
    except ValueError as e:
        try:
            auth_service.refund_quota(db, current_user.id, "create_subscription")
        except Exception as refund_err:
            logger.error(f"退还配额失败: {refund_err}")
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        try:
            auth_service.refund_quota(db, current_user.id, "create_subscription")
        except Exception as refund_err:
            logger.error(f"退还配额失败: {refund_err}")
        logger.error(f"创建订阅失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"创建订阅失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/{subscription_id}")
async def update_subscription(
    subscription_id: int,
    sub_in: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    更新话题订阅
    """
    try:
        subscription = subscription_service.update_subscription(
            db, subscription_id, current_user.id, sub_in
        )
        return success_response(
            data={"subscription": subscription},
            message="更新订阅成功"
        )
    except ValueError as e:
        return _map_value_error(e)


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    删除话题订阅
    """
    try:
        success = subscription_service.delete_subscription(db, subscription_id, current_user.id)
        if success:
            return success_response(
                data={"subscription_id": subscription_id},
                message="删除订阅成功"
            )
        else:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="订阅不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )
    except ValueError as e:
        return _map_value_error(e)
    except Exception as e:
        logger.error(f"删除订阅失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"删除订阅失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/{subscription_id}/pause")
async def pause_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    暂停话题订阅
    """
    try:
        subscription = subscription_service.pause_subscription(db, subscription_id, current_user.id)
        return success_response(
            data={"subscription": subscription},
            message="暂停订阅成功"
        )
    except ValueError as e:
        return _map_value_error(e)
    except Exception as e:
        logger.error(f"暂停订阅失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"暂停订阅失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/{subscription_id}/resume")
async def resume_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    恢复话题订阅
    """
    try:
        subscription = subscription_service.resume_subscription(db, subscription_id, current_user.id)
        return success_response(
            data={"subscription": subscription},
            message="恢复订阅成功"
        )
    except ValueError as e:
        return _map_value_error(e)
    except Exception as e:
        logger.error(f"恢复订阅失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"恢复订阅失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/push/records")
async def get_push_records(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    获取用户的推送记录
    """
    try:
        records = subscription_service.get_user_push_records(
            db, current_user.id, unread_only=unread_only
        )
        return success_response(
            data={"records": records, "total": len(records)},
            message="获取推送记录成功"
        )
    except Exception as e:
        logger.error(f"获取推送记录失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取推送记录失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/push/records/{record_id}/read")
async def mark_record_as_read(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    标记推送记录为已读
    """
    try:
        record = subscription_service.mark_as_read(db, record_id, current_user.id)
        return success_response(
            data={"record": record},
            message="标记已读成功"
        )
    except ValueError as e:
        return _map_value_error(e)
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"标记已读失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/push/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    获取用户未读推送数量
    """
    try:
        count = subscription_service.get_unread_count(db, current_user.id)
        return success_response(
            data={"count": count},
            message="获取未读数量成功"
        )
    except Exception as e:
        logger.error(f"获取未读数量失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取未读数量失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return success_response(data={"status": "ok"}, message="话题订阅服务正常")


@router.post("/push/trigger")
async def trigger_push_now(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    手动触发订阅推送（仅 admin 可用）

    开发/测试用：不等 08:00 定时任务，立即扫描到期订阅并推送。
    生产环境通过 admin 权限隔离，普通用户无法触发。
    """
    if not current_user.is_admin:
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="仅管理员可手动触发推送",
            status_code=status.HTTP_403_FORBIDDEN
        )

    from backend.services.subscription_scheduler_service import run_push_cycle
    try:
        count = await run_push_cycle(db)
        return success_response(
            data={"triggered": True, "count": count},
            message=f"推送任务已执行，处理 {count} 个订阅"
        )
    except Exception as e:
        logger.error(f"手动触发推送失败: {e}", exc_info=True)
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"触发推送失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
