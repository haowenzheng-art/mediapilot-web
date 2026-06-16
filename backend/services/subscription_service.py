"""
话题订阅服务
"""
import logging
from typing import List
from sqlalchemy.orm import Session

from backend.repository.subscription_repo import SubscriptionRepository, PushRecordRepository
from backend.models.domain.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse,
    PushRecordResponse
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """话题订阅业务服务"""

    def __init__(self):
        self._sub_repo = None
        self._push_repo = None

    def _get_sub_repo(self, db: Session) -> SubscriptionRepository:
        """获取订阅repository实例"""
        if self._sub_repo is None or self._sub_repo.db != db:
            self._sub_repo = SubscriptionRepository(db)
        return self._sub_repo

    def _get_push_repo(self, db: Session) -> PushRecordRepository:
        """获取推送记录repository实例"""
        if self._push_repo is None or self._push_repo.db != db:
            self._push_repo = PushRecordRepository(db)
        return self._push_repo

    def get_user_subscriptions(self, db: Session, user_id: int,
                               include_paused: bool = False) -> List[SubscriptionResponse]:
        """获取用户的订阅列表"""
        repo = self._get_sub_repo(db)
        subscriptions = repo.get_user_subscriptions(user_id, include_paused)
        return [SubscriptionResponse.model_validate(s) for s in subscriptions]

    def create_subscription(self, db: Session, user_id: int, sub_in: SubscriptionCreate) -> SubscriptionResponse:
        """创建订阅"""
        repo = self._get_sub_repo(db)

        # 检查是否已存在相同话题
        existing = repo.get_by_topic(user_id, sub_in.topic)
        if existing:
            raise ValueError("已存在相同话题的订阅")

        subscription = repo.create(
            user_id=user_id,
            topic=sub_in.topic,
            description=sub_in.description,
            frequency=sub_in.frequency.value,
            status="active"
        )
        return SubscriptionResponse.model_validate(subscription)

    def update_subscription(self, db: Session, subscription_id: int,
                           user_id: int, sub_in: SubscriptionUpdate) -> SubscriptionResponse:
        """更新订阅"""
        repo = self._get_sub_repo(db)
        subscription = repo.get_by_id(subscription_id)

        if not subscription:
            raise ValueError("订阅不存在")

        if subscription.user_id != user_id:
            raise ValueError("无权修改此订阅")

        update_data = {}
        if sub_in.topic is not None:
            update_data["topic"] = sub_in.topic
        if sub_in.description is not None:
            update_data["description"] = sub_in.description
        if sub_in.frequency is not None:
            update_data["frequency"] = sub_in.frequency.value
            # 更新频率时重新计算下次推送时间
            if sub_in.frequency.value == "daily":
                update_data["next_push_at"] = repo._calculate_next_push("daily")
            elif sub_in.frequency.value == "every_3_days":
                update_data["next_push_at"] = repo._calculate_next_push("every_3_days")
        if sub_in.status is not None:
            update_data["status"] = sub_in.status.value

        subscription = repo.update(subscription, **update_data)
        return SubscriptionResponse.model_validate(subscription)

    def delete_subscription(self, db: Session, subscription_id: int, user_id: int) -> bool:
        """删除订阅"""
        repo = self._get_sub_repo(db)
        subscription = repo.get_by_id(subscription_id)

        if not subscription:
            raise ValueError("订阅不存在")

        if subscription.user_id != user_id:
            raise ValueError("无权删除此订阅")

        return repo.delete(subscription_id)

    def pause_subscription(self, db: Session, subscription_id: int, user_id: int) -> SubscriptionResponse:
        """暂停订阅"""
        repo = self._get_sub_repo(db)
        subscription = repo.get_by_id(subscription_id)

        if not subscription:
            raise ValueError("订阅不存在")

        if subscription.user_id != user_id:
            raise ValueError("无权暂停此订阅")

        subscription = repo.update(subscription, status="paused")
        return SubscriptionResponse.model_validate(subscription)

    def resume_subscription(self, db: Session, subscription_id: int, user_id: int) -> SubscriptionResponse:
        """恢复订阅"""
        repo = self._get_sub_repo(db)
        subscription = repo.get_by_id(subscription_id)

        if not subscription:
            raise ValueError("订阅不存在")

        if subscription.user_id != user_id:
            raise ValueError("无权恢复此订阅")

        # 重新计算下次推送时间
        frequency = subscription.frequency
        next_push = repo._calculate_next_push(frequency)

        subscription = repo.update(subscription, status="active", next_push_at=next_push)
        return SubscriptionResponse.model_validate(subscription)

    def get_user_push_records(self, db: Session, user_id: int, limit: int = 50,
                              unread_only: bool = False) -> List[PushRecordResponse]:
        """获取用户的推送记录"""
        repo = self._get_push_repo(db)
        records = repo.get_user_push_records(user_id, limit, unread_only)
        return [PushRecordResponse.model_validate(r) for r in records]

    def mark_as_read(self, db: Session, record_id: int, user_id: int) -> PushRecordResponse:
        """标记推送记录为已读"""
        repo = self._get_push_repo(db)
        record = repo.get_by_id(record_id)

        if not record:
            raise ValueError("推送记录不存在")

        # 检查权限
        if record.subscription.user_id != user_id:
            raise ValueError("无权标记此推送记录")

        record = repo.mark_as_read(record_id)
        return PushRecordResponse.model_validate(record)

    def mark_subscription_as_read(self, db: Session, subscription_id: int, user_id: int) -> int:
        """将订阅的所有未读记录标记为已读"""
        repo = self._get_sub_repo(db)
        subscription = repo.get_by_id(subscription_id)

        if not subscription:
            raise ValueError("订阅不存在")

        if subscription.user_id != user_id:
            raise ValueError("无权操作此订阅")

        push_repo = self._get_push_repo(db)
        return push_repo.mark_subscription_as_read(subscription_id)

    def get_unread_count(self, db: Session, user_id: int) -> int:
        """获取用户未读推送数量"""
        repo = self._get_push_repo(db)
        return repo.get_unread_count(user_id)

    def get_due_subscriptions(self, db: Session) -> List[SubscriptionResponse]:
        """获取需要推送的订阅（用于定时任务）"""
        repo = self._get_sub_repo(db)
        subscriptions = repo.get_due_subscriptions()
        return [SubscriptionResponse.model_validate(s) for s in subscriptions]

    def create_push_record(self, db: Session, subscription_id: int,
                           topic: str, hot_topic_data: dict) -> PushRecordResponse:
        """创建推送记录"""
        repo = self._get_push_repo(db)
        record = repo.create(subscription_id, topic, hot_topic_data)
        return PushRecordResponse.model_validate(record)

    def update_subscription_push_time(self, db: Session, subscription_id: int) -> SubscriptionResponse:
        """更新订阅的推送时间"""
        repo = self._get_sub_repo(db)
        subscription = repo.get_by_id(subscription_id)

        if not subscription:
            raise ValueError("订阅不存在")

        subscription = repo.update_last_pushed(subscription)
        return SubscriptionResponse.model_validate(subscription)


# 全局实例
subscription_service = SubscriptionService()