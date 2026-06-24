"""
日历服务
处理日历事件的 CRUD 操作
添加分页和事务管理
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.database.tables import CalendarEventTable
from backend.models.domain.calendar import CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse
from backend.config.database import TransactionManager
import logging

logger = logging.getLogger(__name__)


class CalendarService:
    """日历服务"""

    def __init__(self):
        """初始化日历服务"""
        pass

    def create_event(
        self,
        db: Session,
        user_id: int,
        event_data: CalendarEventCreate
    ) -> CalendarEventResponse:
        """
        创建日历事件（带事务管理）

        Args:
            db: 数据库会话
            user_id: 用户 ID
            event_data: 事件创建数据

        Returns:
            创建的事件响应

        Raises:
            ValueError: 参数验证失败
        """
        # 验证状态值
        valid_statuses = ["pending", "completed", "cancelled", "in_progress"]
        if event_data.status not in valid_statuses:
            raise ValueError(f"状态值无效，应为: {', '.join(valid_statuses)}")

        # 使用事务管理器
        with TransactionManager(db):
            # 创建事件
            new_event = CalendarEventTable(
                user_id=user_id,
                title=event_data.title,
                content=event_data.content,
                scheduled_date=event_data.scheduled_date,
                platform=event_data.platform,
                status=event_data.status
            )

            db.add(new_event)
            db.flush()  # 刷新获取 ID

            logger.info(f"创建日历事件成功: event_id={new_event.id}, user_id={user_id}")

            return CalendarEventResponse.model_validate(new_event)

    def get_event(
        self,
        db: Session,
        user_id: int,
        event_id: int
    ) -> Optional[CalendarEventResponse]:
        """
        获取单个日历事件

        Args:
            db: 数据库会话
            user_id: 用户 ID
            event_id: 事件 ID

        Returns:
            事件响应，不存在则返回 None
        """
        event = db.query(CalendarEventTable).filter(
            CalendarEventTable.id == event_id,
            CalendarEventTable.user_id == user_id
        ).first()

        if event:
            return CalendarEventResponse.model_validate(event)
        return None

    def get_events(
        self,
        db: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[CalendarEventResponse], int]:
        """
        获取用户的日历事件列表（支持分页）

        Args:
            db: 数据库会话
            user_id: 用户 ID
            start_date: 开始日期
            end_date: 结束日期
            status: 状态筛选
            page: 页码（默认值：1）
            per_page: 每页数量（默认值：20）

        Returns:
            (事件列表, 总数)
        """
        query = db.query(CalendarEventTable).filter(
            CalendarEventTable.user_id == user_id
        )

        # 日期范围筛选
        if start_date:
            query = query.filter(CalendarEventTable.scheduled_date >= start_date)

        if end_date:
            query = query.filter(CalendarEventTable.scheduled_date <= end_date)

        # 状态筛选
        if status:
            query = query.filter(CalendarEventTable.status == status)

        # 获取总数
        total = query.count()

        # 按计划日期升序排序
        query = query.order_by(CalendarEventTable.scheduled_date)

        # 分页
        offset = (page - 1) * per_page
        events = query.offset(offset).limit(per_page).all()

        return (
            [CalendarEventResponse.model_validate(event) for event in events],
            total
        )

    def get_upcoming_events(
        self,
        db: Session,
        user_id: int,
        days: int = 7
    ) -> List[CalendarEventResponse]:
        """
        获取即将到来的事件

        Args:
            db: 数据库会话
            user_id: 用户 ID
            days: 未来天数（默认值：7）

        Returns:
            即将到来事件列表
        """
        from datetime import timedelta

        future_date = datetime.utcnow() + timedelta(days=days)

        events = db.query(CalendarEventTable).filter(
            CalendarEventTable.user_id == user_id,
            CalendarEventTable.scheduled_date >= datetime.utcnow(),
            CalendarEventTable.scheduled_date <= future_date,
            CalendarEventTable.status == "pending"
        ).order_by(
            CalendarEventTable.scheduled_date
        ).all()

        return [CalendarEventResponse.model_validate(event) for event in events]

    def update_event(
        self,
        db: Session,
        user_id: int,
        event_id: int,
        event_data: CalendarEventUpdate
    ) -> Optional[CalendarEventResponse]:
        """
        更新日历事件（带事务管理）

        Args:
            db: 数据库会话
            user_id: 用户 ID
            event_id: 事件 ID
            event_data: 事件更新数据

        Returns:
            更新后的事件响应，不存在则返回 None
        """
        # 使用事务管理器
        with TransactionManager(db):
            event = db.query(CalendarEventTable).filter(
                CalendarEventTable.id == event_id,
                CalendarEventTable.user_id == user_id
            ).first()

            if not event:
                return None

            # 更新字段
            if event_data.title is not None:
                event.title = event_data.title
            if event_data.content is not None:
                event.content = event_data.content
            if event_data.scheduled_date is not None:
                event.scheduled_date = event_data.scheduled_date
            if event_data.platform is not None:
                event.platform = event_data.platform
            if event_data.status is not None:
                # 验证状态值
                valid_statuses = ["pending", "completed", "cancelled", "in_progress"]
                if event_data.status not in valid_statuses:
                    raise ValueError(f"状态值无效，应为: {', '.join(valid_statuses)}")
                event.status = event_data.status

            db.flush()

            logger.info(f"更新日历事件成功: event_id={event_id}")

            return CalendarEventResponse.model_validate(event)

    def delete_event(
        self,
        db: Session,
        user_id: int,
        event_id: int
    ) -> bool:
        """
        删除日历事件（带事务管理）

        Args:
            db: 数据库会话
            user_id: 用户 ID
            event_id: 事件 ID

        Returns:
            是否成功删除
        """
        # 使用事务管理器
        with TransactionManager(db):
            event = db.query(CalendarEventTable).filter(
                CalendarEventTable.id == event_id,
                CalendarEventTable.user_id == user_id
            ).first()

            if not event:
                return False

            db.delete(event)
            db.flush()

            logger.info(f"删除日历事件成功: event_id={event_id}")

            return True


# 全局实例
calendar_service = CalendarService()
