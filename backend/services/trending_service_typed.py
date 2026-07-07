"""
热点搜索业务逻辑
使用 Python 类型提示，遵循 PEP 8 标准
"""
import logging
from typing import Optional, List, Dict, Any

from backend.models.schemas.response import HotTopicResponse, TrendingSearchResponse
from backend.services.mock_data import MockDataService
from backend.core.platform_api import get_platform_api_manager

logger = logging.getLogger(__name__)


class TrendingService:
    """
    热点搜索服务

    提供热点话题搜索功能，支持多平台数据聚合
    """

    def __init__(self) -> None:
        """初始化服务"""
        self.mock_data = MockDataService()
        self.platform_api = get_platform_api_manager().get_hot_topic_api()

    async def search(
        self,
        keyword: str,
        platforms: List[str],
        days: int = 7
    ) -> TrendingSearchResponse:
        """
        搜索热点话题

        Args:
            keyword: 搜索关键词
            platforms: 平台列表（抖音、微博、小红书等）
            days: 搜索天数

        Returns:
            TrendingSearchResponse: 热点搜索响应
        """
        try:
            # 优先使用平台API（v3 改造：返回 HotTopicSearchResult）
            from backend.core.platform_api import HotTopicSearchResult
            search_result = await self.platform_api.search_hot_topics(
                keyword=keyword,
                platforms=platforms,
                days=days
            )
            # 兼容老签名（list 格式）和新签名（HotTopicSearchResult）
            if isinstance(search_result, HotTopicSearchResult):
                topics = search_result.topics
                degraded_platforms = search_result.degraded_platforms
                sixty_failed_platforms = search_result.sixty_failed_platforms
                used_cache = search_result.used_cache
                cached_at = search_result.cached_at
                freshness = search_result.freshness
            else:
                # 兼容老调用
                topics = search_result
                degraded_platforms = []
                sixty_failed_platforms = []
                used_cache = False
                cached_at = None
                freshness = "fresh"
        except Exception as e:
            # API调用失败，降级到mock数据
            logger.warning(f"平台API调用失败，使用mock数据: {e}")
            topics = self.mock_data.search_trending(
                keyword=keyword,
                platforms=platforms,
                days=days
            )
            degraded_platforms = []
            sixty_failed_platforms = []
            used_cache = False
            cached_at = None
            freshness = "degraded"

        hot_topics: List[HotTopicResponse] = []
        if isinstance(topics, list):
            # 处理列表格式响应（platform_api 直接返回列表）
            hot_topics = [
                HotTopicResponse(**t) if isinstance(t, dict) else t
                for t in topics
            ]
        elif isinstance(topics, dict):
            # 处理字典格式响应
            if hasattr(topics, 'hot_topics'):
                hot_topics = [
                    HotTopicResponse(**t) if isinstance(t, dict) else t
                    for t in topics.hot_topics
                ]
            else:
                hot_topics = []

        from datetime import datetime
        cached_at_dt = datetime.fromtimestamp(cached_at) if cached_at else None
        return TrendingSearchResponse(
            keyword=keyword,
            total_count=len(hot_topics),
            hot_topics=hot_topics,
            degraded_platforms=degraded_platforms,
            sixty_failed_platforms=sixty_failed_platforms,
            used_cache=used_cache,
            cached_at=cached_at_dt,
            freshness=freshness,
        )


class MockDataService:
    """
    Mock 数据服务（用于API失败时的降级）
    """

    @staticmethod
    def search_trending(
        keyword: str,
        platforms: List[str],
        days: int
    ) -> List[Dict[str, Any]]:
        """
        生成模拟热点数据
        """
        mock_topics: List[Dict[str, Any]] = []

        for platform in platforms:
            for i in range(min(5, days)):  # 生成模拟数据
                mock_topic = {
                    "title": f"{keyword} 相关话题 {i+1}",
                    "heat_index": (days * 10) + i,
                    "platform": platform,
                    "trend": "stable",
                    "summary": f"这是关于 {keyword} 的模拟热点话题",
                    "url": f"https://example.com/{platform}/topic/{i+1}",
            }
                mock_topics.append(mock_topic)

        return mock_topics
