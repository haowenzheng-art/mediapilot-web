"""
内容库数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta

from backend.models.database.tables import ContentTable, HotTopicTrendTable


class ContentLibraryRepository:
    """内容库数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, content_id: int) -> Optional[ContentTable]:
        """根据ID获取内容"""
        return self.db.query(ContentTable).filter(
            ContentTable.id == content_id
        ).first()

    def get_by_content_id(self, content_type: str, content_uuid: str) -> Optional[ContentTable]:
        """根据内容类型和UUID获取内容"""
        return self.db.query(ContentTable).filter(
            and_(
                ContentTable.content_type == content_type,
                ContentTable.content_id == content_uuid
            )
        ).first()

    def get_user_contents(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        is_processed: Optional[bool] = None,
        hot_topic_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ContentTable]:
        """获取用户的内容列表"""
        query = self.db.query(ContentTable).filter(ContentTable.user_id == user_id)

        if content_type:
            query = query.filter(ContentTable.content_type == content_type)

        if is_processed is not None:
            query = query.filter(ContentTable.is_processed == is_processed)

        if hot_topic_id:
            query = query.filter(ContentTable.hot_topic_id == hot_topic_id)

        return query.order_by(ContentTable.created_at.desc()).limit(limit).offset(offset).all()

    def get_hot_topic_contents(
        self,
        hot_topic_id: str,
        user_id: int,
        limit: int = 20
    ) -> List[ContentTable]:
        """获取热点关联的内容"""
        return self.db.query(ContentTable).filter(
            and_(
                ContentTable.hot_topic_id == hot_topic_id,
                ContentTable.user_id == user_id
            )
        ).order_by(ContentTable.created_at.desc()).limit(limit).all()

    def create(
        self,
        user_id: int,
        content_type: str,
        content_uuid: str,
        title: str,
        summary: Optional[str] = None,
        hot_topic_id: Optional[str] = None,
        hot_topic_title: Optional[str] = None,
        hot_topic_source: Optional[str] = None,
        mode: Optional[str] = None,
        persona: Optional[str] = None,
        platform: Optional[str] = None,
        style: Optional[str] = None
    ) -> ContentTable:
        """创建内容记录"""
        content = ContentTable(
            user_id=user_id,
            content_type=content_type,
            content_id=content_uuid,
            title=title,
            summary=summary,
            hot_topic_id=hot_topic_id,
            hot_topic_title=hot_topic_title,
            hot_topic_source=hot_topic_source,
            mode=mode,
            persona=persona,
            platform=platform,
            style=style,
            is_processed=False
        )
        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)
        return content

    def update(self, content: ContentTable, **kwargs) -> ContentTable:
        """更新内容记录"""
        for field, value in kwargs.items():
            if hasattr(content, field):
                setattr(content, field, value)
        self.db.commit()
        self.db.refresh(content)
        return content

    def mark_as_processed(self, content_id: int) -> Optional[ContentTable]:
        """标记为已处理"""
        content = self.get_by_id(content_id)
        if content:
            content.is_processed = True
            content.processed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(content)
        return content

    def delete(self, content_id: int) -> bool:
        """删除内容记录"""
        content = self.get_by_id(content_id)
        if content:
            self.db.delete(content)
            self.db.commit()
            return True
        return False

    def count_user_contents(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        is_processed: Optional[bool] = None
    ) -> int:
        """统计用户内容数量"""
        query = self.db.query(ContentTable).filter(ContentTable.user_id == user_id)

        if content_type:
            query = query.filter(ContentTable.content_type == content_type)

        if is_processed is not None:
            query = query.filter(ContentTable.is_processed == is_processed)

        return query.count()


class HotTopicTrendRepository:
    """热点趋势数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        hot_topic_id: str,
        hot_topic_title: Optional[str] = None,
        hot_topic_source: Optional[str] = None,
        heat_score: Optional[int] = None,
        trend_direction: Optional[str] = None
    ) -> HotTopicTrendTable:
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

    def get_topic_trends(
        self,
        hot_topic_id: str,
        limit: int = 100
    ) -> List[HotTopicTrendTable]:
        """获取话题的历史趋势"""
        return self.db.query(HotTopicTrendTable).filter(
            HotTopicTrendTable.hot_topic_id == hot_topic_id
        ).order_by(HotTopicTrendTable.recorded_at.desc()).limit(limit).all()

    def get_recent_trends(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[HotTopicTrendTable]:
        """获取最近的热点趋势"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(HotTopicTrendTable).filter(
            HotTopicTrendTable.recorded_at >= cutoff
        ).order_by(HotTopicTrendTable.recorded_at.desc()).limit(limit).all()

    def batch_create(self, trends_data: List[dict]) -> int:
        """批量创建趋势记录"""
        count = 0
        for data in trends_data:
            trend = HotTopicTrendTable(
                hot_topic_id=data.get("hot_topic_id"),
                hot_topic_title=data.get("hot_topic_title"),
                hot_topic_source=data.get("hot_topic_source"),
                heat_score=data.get("heat_score"),
                trend_direction=data.get("trend_direction")
            )
            self.db.add(trend)
            count += 1
        self.db.commit()
        return count

    def delete_old_trends(self, days: int = 30) -> int:
        """删除旧的趋势记录"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = self.db.query(HotTopicTrendTable).filter(
            HotTopicTrendTable.recorded_at < cutoff
        ).delete()
        self.db.commit()
        return count