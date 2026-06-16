"""
话题订阅数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta

from backend.models.database.tables import SubscriptionTable, PushRecordTable


class SubscriptionRepository:
    """话题订阅数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, subscription_id: int) -> Optional[SubscriptionTable]:
        """根据ID获取订阅"""
        return self.db.query(SubscriptionTable).filter(
            SubscriptionTable.id == subscription_id
        ).first()

    def get_user_subscriptions(self, user_id: int, include_paused: bool = False) -> List[SubscriptionTable]:
        """获取用户的订阅列表"""
        query = self.db.query(SubscriptionTable).filter(
            SubscriptionTable.user_id == user_id
        )
        if not include_paused:
            query = query.filter(SubscriptionTable.status == "active")
        return query.order_by(SubscriptionTable.created_at.desc()).all()

    def get_by_topic(self, user_id: int, topic: str) -> Optional[SubscriptionTable]:
        """根据话题获取订阅"""
        return self.db.query(SubscriptionTable).filter(
            and_(
                SubscriptionTable.user_id == user_id,
                SubscriptionTable.topic == topic
            )
        ).first()

    def create(self, user_id: int, topic: str, description: str = None,
              frequency: str = "daily", status: str = "active") -> SubscriptionTable:
        """创建订阅"""
        subscription = SubscriptionTable(
            user_id=user_id,
            topic=topic,
            description=description,
            frequency=frequency,
            status=status,
            next_push_at=self._calculate_next_push(frequency)
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update(self, subscription: SubscriptionTable, **kwargs) -> SubscriptionTable:
        """更新订阅"""
        for field, value in kwargs.items():
            if hasattr(subscription, field):
                setattr(subscription, field, value)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def delete(self, subscription_id: int) -> bool:
        """删除订阅"""
        subscription = self.get_by_id(subscription_id)
        if subscription:
            self.db.delete(subscription)
            self.db.commit()
            return True
        return False

    def update_last_pushed(self, subscription: SubscriptionTable) -> SubscriptionTable:
        """更新最后推送时间"""
        subscription.last_pushed_at = datetime.utcnow()
        # 计算下次推送时间
        if subscription.frequency == "daily":
            subscription.next_push_at = datetime.utcnow() + timedelta(days=1)
        elif subscription.frequency == "every_3_days":
            subscription.next_push_at = datetime.utcnow() + timedelta(days=3)

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def get_due_subscriptions(self) -> List[SubscriptionTable]:
        """获取需要推送的订阅"""
        return self.db.query(SubscriptionTable).filter(
            and_(
                SubscriptionTable.status == "active",
                SubscriptionTable.next_push_at <= datetime.utcnow()
            )
        ).all()

    def _calculate_next_push(self, frequency: str) -> datetime:
        """计算下次推送时间"""
        if frequency == "daily":
            return datetime.utcnow() + timedelta(days=1)
        elif frequency == "every_3_days":
            return datetime.utcnow() + timedelta(days=3)
        return datetime.utcnow() + timedelta(days=1)


class PushRecordRepository:
    """推送记录数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, record_id: int) -> Optional[PushRecordTable]:
        """根据ID获取推送记录"""
        return self.db.query(PushRecordTable).filter(
            PushRecordTable.id == record_id
        ).first()

    def create(self, subscription_id: int, topic: str, hot_topic_data: dict) -> PushRecordTable:
        """创建推送记录"""
        record = PushRecordTable(
            subscription_id=subscription_id,
            topic=topic,
            hot_topic_data=hot_topic_data,
            status="new"
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def mark_as_read(self, record_id: int) -> Optional[PushRecordTable]:
        """标记为已读"""
        record = self.get_by_id(record_id)
        if record:
            record.status = "read"
            record.read_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(record)
        return record

    def mark_subscription_as_read(self, subscription_id: int) -> int:
        """将订阅的所有未读记录标记为已读"""
        count = self.db.query(PushRecordTable).filter(
            and_(
                PushRecordTable.subscription_id == subscription_id,
                PushRecordTable.status == "new"
            )
        ).update(
            {"status": "read", "read_at": datetime.utcnow()}
        )
        self.db.commit()
        return count

    def get_user_push_records(self, user_id: int, limit: int = 50,
                            unread_only: bool = False) -> List[PushRecordTable]:
        """获取用户的推送记录"""
        query = self.db.query(PushRecordTable).join(SubscriptionTable).filter(
            SubscriptionTable.user_id == user_id
        )
        if unread_only:
            query = query.filter(PushRecordTable.status == "new")
        return query.order_by(PushRecordTable.pushed_at.desc()).limit(limit).all()

    def get_subscription_push_records(self, subscription_id: int, limit: int = 20) -> List[PushRecordTable]:
        """获取订阅的推送记录"""
        return self.db.query(PushRecordTable).filter(
            PushRecordTable.subscription_id == subscription_id
        ).order_by(PushRecordTable.pushed_at.desc()).limit(limit).all()

    def get_unread_count(self, user_id: int) -> int:
        """获取用户未读推送数量"""
        return self.db.query(PushRecordTable).join(SubscriptionTable).filter(
            and_(
                SubscriptionTable.user_id == user_id,
                PushRecordTable.status == "new"
            )
        ).count()