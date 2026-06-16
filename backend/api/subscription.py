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
    paginated_response
)
from backend.services.subscription_service import subscription_service
from backend.models.database.tables import UserTable
from backend.api.dependencies import get_current_user
from backend.services.auth_service_typed import auth_service
from backend.config.settings import settings, ensure_dev_user

router = APIRouter(prefix="/subscriptions", tags=["话题订阅"])


@router.get("")
async def get_subscriptions(
    db: Session = Depends(get_db)
):
    """
    获取用户的话题订阅列表
    """
    user = ensure_dev_user(db)

    try:
        subscriptions = subscription_service.get_user_subscriptions(db, user.id)
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
    db: Session = Depends(get_db)
):
    """
    创建话题订阅
    """
    user = ensure_dev_user(db)

    # 检查配额
    if not auth_service.check_quota(db, user.id, "create_subscription"):
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        subscription = subscription_service.create_subscription(db, user.id, sub_in)

        # 扣减配额
        auth_service.deduct_quota(db, user.id, "create_subscription")

        return success_response(
            data={"subscription": subscription},
            message="创建订阅成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
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
    db: Session = Depends(get_db)
):
    """
    更新话题订阅
    """
    user = ensure_dev_user(db)

    try:
        subscription = subscription_service.update_subscription(db, subscription_id, user.id, sub_in)
        return success_response(
            data={"subscription": subscription},
            message="更新订阅成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"更新订阅失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"更新订阅失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db)
):
    """
    删除话题订阅
    """
    user = ensure_dev_user(db)

    try:
        success = subscription_service.delete_subscription(db, subscription_id, user.id)
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
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
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
    db: Session = Depends(get_db)
):
    """
    暂停话题订阅
    """
    user = ensure_dev_user(db)

    try:
        subscription = subscription_service.pause_subscription(db, subscription_id, user.id)
        return success_response(
            data={"subscription": subscription},
            message="暂停订阅成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
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
    db: Session = Depends(get_db)
):
    """
    恢复话题订阅
    """
    user = ensure_dev_user(db)

    try:
        subscription = subscription_service.resume_subscription(db, subscription_id, user.id)
        return success_response(
            data={"subscription": subscription},
            message="恢复订阅成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
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
    db: Session = Depends(get_db)
):
    """
    获取用户的推送记录
    """
    user = ensure_dev_user(db)

    try:
        records = subscription_service.get_user_push_records(db, user.id, unread_only=unread_only)
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
    db: Session = Depends(get_db)
):
    """
    标记推送记录为已读
    """
    user = ensure_dev_user(db)

    try:
        record = subscription_service.mark_as_read(db, record_id, user.id)
        return success_response(
            data={"record": record},
            message="标记已读成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"标记已读失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/push/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db)
):
    """
    获取用户未读推送数量
    """
    user = ensure_dev_user(db)

    try:
        count = subscription_service.get_unread_count(db, user.id)
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