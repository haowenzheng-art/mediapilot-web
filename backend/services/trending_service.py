"""
热点搜索业务逻辑
"""
from backend.models.schemas.response import HotTopicResponse, TrendingSearchResponse
from backend.services.mock_data import MockDataService
from backend.core.platform_api import get_platform_api_manager
from backend.models.hot_topics import HotTopic, HotTopicSubscription, HotTopicPush


class TrendingService:
    """热点搜索服务"""

    def __init__(self):
        self.mock_data = MockDataService()
        self.platform_api = get_platform_api_manager().get_hot_topic_api()

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
        try:
            topics = await self.platform_api.search_hot_topics(
                keyword=keyword,
                platforms=platforms,
                days=days
            )
        except Exception as e:
            import logging
            logging.warning(f"平台API调用失败，使用mock数据: {e}")
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

    async def create_subscription(
        self,
        name: str,
        keywords: list,
        frequency: str
    ) -> HotTopicSubscription:
        """创建话题订阅

        Args:
            name: 订阅名称
            keywords: 搜索关键词列表
            frequency: 更新频率（daily/every3days）

        Returns:
            订阅对象
        """
        return HotTopicSubscription(
            id=f"sub-{name.lower().replace(' ', '-')}",
            name=name,
            keywords=keywords,
            update_frequency=frequency,
            last_updated_at=None,
            is_active=True
        )

    async def get_subscriptions(self) -> list[HotTopicSubscription]:
        """获取用户的所有订阅"""
        return []

    async def get_active_pushes(self) -> list[HotTopicPush]:
        """获取待推送的热点"""
        return []

    async def mark_push_read(self, push_id: str):
        """标记推送为已读"""
        pass

    async def create_daily_push_task(self):
        """创建每日自动推送任务（由APScheduler调度）"""
        pass
