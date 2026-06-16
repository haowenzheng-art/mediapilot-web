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
            # 优先使用平台API
            topics = await self.platform_api.search_hot_topics(
                keyword=keyword,
                platforms=platforms,
                days=days
            )
        except Exception as e:
            # API调用失败，降级到mock数据
            logger.warning(f"平台API调用失败，使用mock数据: {e}")
            topics = self.mock_data.search_trending(
                keyword=keyword,
                platforms=platforms,
                days=days
            )

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

        return TrendingSearchResponse(
            keyword=keyword,
            total_count=len(hot_topics),
            hot_topics=hot_topics
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
