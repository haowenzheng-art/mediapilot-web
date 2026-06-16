"""
内容库数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime

from backend.models.database.tables import ContentTable, HotTopicTrendTable


class ContentRepository:
    """内容数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, content_id: int) -> Optional[ContentTable]:
        """根据ID获取内容"""
        return self.db.query(ContentTable).filter(
            ContentTable.id == content_id
        ).first()

    def get_by_content_id(self, content_id: str, user_id: int) -> Optional[ContentTable]:
        """根据内容ID获取内容"""
        return self.db.query(ContentTable).filter(
            and_(
                ContentTable.content_id == content_id,
                ContentTable.user_id == user_id
            )
        ).first()

    def get_user_contents(self, user_id: int, content_type: str = None,
                          is_processed: bool = None, limit: int = 50) -> List[ContentTable]:
        """获取用户的内容列表"""
        query = self.db.query(ContentTable).filter(
            ContentTable.user_id == user_id
        )

        if content_type:
            query = query.filter(ContentTable.content_type == content_type)

        if is_processed is not None:
            query = query.filter(ContentTable.is_processed == is_processed)

        return query.order_by(ContentTable.created_at.desc()).limit(limit).all()

    def get_by_hot_topic(self, hot_topic_id: str, user_id: int) -> List[ContentTable]:
        """根据热点ID获取相关内容"""
        return self.db.query(ContentTable).filter(
            and_(
                ContentTable.hot_topic_id == hot_topic_id,
                ContentTable.user_id == user_id
            )
        ).order_by(ContentTable.created_at.desc()).all()

    def create(self, user_id: int, content_type: str, content_id: str, title: str,
               hot_topic_id: str = None, hot_topic_title: str = None,
               hot_topic_source: str = None, summary: str = None,
               mode: str = None, persona: str = None, platform: str = None,
               style: str = None, is_processed: bool = False) -> ContentTable:
        """创建内容"""
        content = ContentTable(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            hot_topic_id=hot_topic_id,
            hot_topic_title=hot_topic_title,
            hot_topic_source=hot_topic_source,
            title=title,
            summary=summary,
            mode=mode,
            persona=persona,
            platform=platform,
            style=style,
            is_processed=is_processed
        )
        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)
        return content

    def update(self, content: ContentTable, **kwargs) -> ContentTable:
        """更新内容"""
        for field, value in kwargs.items():
            if hasattr(content, field):
                setattr(content, field, value)

        # 如果标记为已处理，更新 processed_at
        if kwargs.get('is_processed') and not content.is_processed:
            content.processed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(content)
        return content

    def mark_as_processed(self, content_id: int) -> Optional[ContentTable]:
        """标记为已处理"""
        content = self.get_by_id(content_id)
        if content and not content.is_processed:
            content.is_processed = True
            content.processed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(content)
        return content

    def delete(self, content_id: int) -> bool:
        """删除内容"""
        content = self.get_by_id(content_id)
        if content:
            self.db.delete(content)
            self.db.commit()
            return True
        return False


class HotTopicTrendRepository:
    """热点趋势数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, trend_id: int) -> Optional[HotTopicTrendTable]:
        """根据ID获取趋势记录"""
        return self.db.query(HotTopicTrendTable).filter(
            HotTopicTrendTable.id == trend_id
        ).first()

    def get_topic_trends(self, hot_topic_id: str, start_date: datetime = None,
                         end_date: datetime = None, limit: int = 100) -> List[HotTopicTrendTable]:
        """获取话题的趋势历史"""
        query = self.db.query(HotTopicTrendTable).filter(
            HotTopicTrendTable.hot_topic_id == hot_topic_id
        )

        if start_date:
            query = query.filter(HotTopicTrendTable.recorded_at >= start_date)

        if end_date:
            query = query.filter(HotTopicTrendTable.recorded_at <= end_date)

        return query.order_by(HotTopicTrendTable.recorded_at.asc()).limit(limit).all()

    def create(self, hot_topic_id: str, heat_score: int = None,
               trend_direction: str = None, hot_topic_title: str = None,
               hot_topic_source: str = None) -> HotTopicTrendTable:
        """创建趋势记录"""
        trend = HotTopicTrendTable(
            hot_topic_id=hot_topic_id,
            hot_topic_title=hot_topic_title,
            hot_topic_source=hot_topic_source,
            heat_score=heat_score,
            trend_direction=trend_direction
        )
        self.db.add(trend)
        self.db.commit()
        self.db.refresh(trend)
        return trend

    def get_latest_trend(self, hot_topic_id: str) -> Optional[HotTopicTrendTable]:
        """获取话题的最新趋势记录"""
        return self.db.query(HotTopicTrendTable).filter(
            HotTopicTrendTable.hot_topic_id == hot_topic_id
        ).order_by(HotTopicTrendTable.recorded_at.desc()).first()

    def delete_topic_trends(self, hot_topic_id: str) -> int:
        """删除话题的所有趋势记录"""
        count = self.db.query(HotTopicTrendTable).filter(
            HotTopicTrendTable.hot_topic_id == hot_topic_id
        ).delete()
        self.db.commit()
        return count