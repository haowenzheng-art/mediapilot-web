"""
热点搜索业务逻辑
"""
from models.domain import HotTopic
from models.schemas.response import HotTopicResponse, TrendingSearchResponse
from models.schemas.response import APIResponse
from services.mock_data import MockDataService


class TrendingService:
    """热点搜索服务"""

    def __init__(self):
        self.mock_data = MockDataService()

    async def search(
        self,
        keyword: str,
        platforms: list,
        days: int
    ) -> TrendingSearchResponse:
        """
        搜索热点话题

        Args:
            keyword: 搜索关键词
            platforms: 平台列表
            days: 搜索天数

        Returns:
            热点搜索响应
        """
        topics = self.mock_data.search_trending(
            keyword=keyword,
            platforms=platforms,
            days=days
        )

        hot_topics = [HotTopicResponse(**t) for t in topics]

        return TrendingSearchResponse(
            keyword=keyword,
            total_count=len(hot_topics),
            hot_topics=hot_topics
        )
