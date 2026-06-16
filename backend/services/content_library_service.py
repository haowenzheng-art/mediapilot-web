"""
内容库服务
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from backend.repository.content_library_repo import ContentLibraryRepository, HotTopicTrendRepository
from backend.models.domain.content_library import (
    ContentCreate, ContentUpdate, ContentResponse,
    TopicHistoryRequest, TrendRecordResponse, TopicHistoryResponse,
    ContentType
)

logger = logging.getLogger(__name__)


class ContentLibraryService:
    """内容库业务服务"""

    def __init__(self):
        self._content_repo = None
        self._trend_repo = None

    def _get_content_repo(self, db: Session) -> ContentLibraryRepository:
        """获取内容库repository实例"""
        if self._content_repo is None or self._content_repo.db != db:
            self._content_repo = ContentLibraryRepository(db)
        return self._content_repo

    def _get_trend_repo(self, db: Session) -> HotTopicTrendRepository:
        """获取趋势repository实例"""
        if self._trend_repo is None or self._trend_repo.db != db:
            self._trend_repo = HotTopicTrendRepository(db)
        return self._trend_repo

    def get_user_contents(
        self,
        db: Session,
        user_id: int,
        content_type: Optional[ContentType] = None,
        is_processed: Optional[bool] = None,
        hot_topic_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ContentResponse]:
        """获取用户的内容列表"""
        repo = self._get_content_repo(db)
        content_type_str = content_type.value if content_type else None
        contents = repo.get_user_contents(
            user_id=user_id,
            content_type=content_type_str,
            is_processed=is_processed,
            hot_topic_id=hot_topic_id,
            limit=limit,
            offset=offset
        )
        return [ContentResponse.model_validate(c) for c in contents]

    def get_content_by_id(self, db: Session, content_id: int) -> Optional[ContentResponse]:
        """根据ID获取内容"""
        repo = self._get_content_repo(db)
        content = repo.get_by_id(content_id)
        if content:
            return ContentResponse.model_validate(content)
        return None

    def create_content(
        self,
        db: Session,
        user_id: int,
        content_in: ContentCreate
    ) -> ContentResponse:
        """创建内容记录"""
        repo = self._get_content_repo(db)
        content = repo.create(
            user_id=user_id,
            content_type=content_in.content_type.value,
            content_uuid=content_in.content_id,
            title=content_in.title,
            summary=content_in.summary,
            hot_topic_id=content_in.hot_topic_id,
            hot_topic_title=content_in.hot_topic_title,
            hot_topic_source=content_in.hot_topic_source,
            mode=content_in.mode,
            persona=content_in.persona,
            platform=content_in.platform,
            style=content_in.style
        )
        return ContentResponse.model_validate(content)

    def update_content(
        self,
        db: Session,
        content_id: int,
        user_id: int,
        content_in: ContentUpdate
    ) -> ContentResponse:
        """更新内容记录"""
        repo = self._get_content_repo(db)
        content = repo.get_by_id(content_id)

        if not content:
            raise ValueError("内容不存在")

        if content.user_id != user_id:
            raise ValueError("无权修改此内容")

        update_data = {}
        if content_in.title is not None:
            update_data["title"] = content_in.title
        if content_in.summary is not None:
            update_data["summary"] = content_in.summary
        if content_in.persona is not None:
            update_data["persona"] = content_in.persona
        if content_in.platform is not None:
            update_data["platform"] = content_in.platform
        if content_in.style is not None:
            update_data["style"] = content_in.style

        content = repo.update(content, **update_data)
        return ContentResponse.model_validate(content)

    def delete_content(self, db: Session, content_id: int, user_id: int) -> bool:
        """删除内容记录"""
        repo = self._get_content_repo(db)
        content = repo.get_by_id(content_id)

        if not content:
            raise ValueError("内容不存在")

        if content.user_id != user_id:
            raise ValueError("无权删除此内容")

        return repo.delete(content_id)

    def mark_as_processed(self, db: Session, content_id: int, user_id: int) -> ContentResponse:
        """标记内容为已处理"""
        repo = self._get_content_repo(db)
        content = repo.get_by_id(content_id)

        if not content:
            raise ValueError("内容不存在")

        if content.user_id != user_id:
            raise ValueError("无权标记此内容")

        content = repo.mark_as_processed(content_id)
        return ContentResponse.model_validate(content)

    def get_hot_topic_contents(
        self,
        db: Session,
        hot_topic_id: str,
        user_id: int,
        limit: int = 20
    ) -> List[ContentResponse]:
        """获取热点关联的内容"""
        repo = self._get_content_repo(db)
        contents = repo.get_hot_topic_contents(hot_topic_id, user_id, limit)
        return [ContentResponse.model_validate(c) for c in contents]

    def count_user_contents(
        self,
        db: Session,
        user_id: int,
        content_type: Optional[ContentType] = None,
        is_processed: Optional[bool] = None
    ) -> int:
        """统计用户内容数量"""
        repo = self._get_content_repo(db)
        content_type_str = content_type.value if content_type else None
        return repo.count_user_contents(user_id, content_type_str, is_processed)

    def get_topic_history(
        self,
        db: Session,
        hot_topic_id: str,
        limit: int = 100
    ) -> TopicHistoryResponse:
        """获取话题的历史趋势"""
        repo = self._get_trend_repo(db)
        trends = repo.get_topic_trends(hot_topic_id, limit)

        hot_topic_title = None
        if trends:
            hot_topic_title = trends[0].hot_topic_title

        return TopicHistoryResponse(
            hot_topic_id=hot_topic_id,
            hot_topic_title=hot_topic_title,
            trends=[TrendRecordResponse.model_validate(t) for t in trends]
        )

    def save_hot_topic_trend(
        self,
        db: Session,
        hot_topic_id: str,
        hot_topic_title: Optional[str] = None,
        hot_topic_source: Optional[str] = None,
        heat_score: Optional[int] = None,
        trend_direction: Optional[str] = None
    ) -> TrendRecordResponse:
        """保存热点趋势"""
        repo = self._get_trend_repo(db)
        trend = repo.create(
            hot_topic_id=hot_topic_id,
            hot_topic_title=hot_topic_title,
            hot_topic_source=hot_topic_source,
            heat_score=heat_score,
            trend_direction=trend_direction
        )
        return TrendRecordResponse.model_validate(trend)

    def batch_save_hot_topic_trends(
        self,
        db: Session,
        trends_data: List[dict]
    ) -> int:
        """批量保存热点趋势"""
        repo = self._get_trend_repo(db)
        return repo.batch_create(trends_data)

    def cleanup_old_trends(self, db: Session, days: int = 30) -> int:
        """清理旧的趋势记录"""
        repo = self._get_trend_repo(db)
        return repo.delete_old_trends(days)


# 全局实例
content_library_service = ContentLibraryService()