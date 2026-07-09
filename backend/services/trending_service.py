"""
热点搜索业务逻辑

v4 改造：
- 接收 HotTopicSearchResult（含 degraded 元信息，sixty_failed 字段保留兼容但固定为空）
- 简化为按源数平均配额
- TrendingSearchResponse 透传 degraded_platforms / freshness / cached_at
"""
import logging
import math
from collections import defaultdict

from backend.models.schemas.response import HotTopicResponse, TrendingSearchResponse
from backend.core.platform_api import get_platform_api_manager, HotTopicSearchResult
from backend.models.hot_topics import HotTopic, HotTopicSubscription, HotTopicPush

logger = logging.getLogger(__name__)


class TrendingService:
    """热点搜索服务"""

    def __init__(self):
        self.platform_api = get_platform_api_manager().get_hot_topic_api()

    async def search(
        self,
        keyword: str,
        platforms: list,
        days: int
    ) -> TrendingSearchResponse:
        """
        搜索热点话题（v3 改造：返回结果携带 degraded/freshness 元信息）

        Args:
            keyword: 搜索关键词
            platforms: 平台列表
            days: 搜索天数

        Returns:
            热点搜索响应
        """
        # 真实数据源失败时返回空，不再回退 mock。
        # mock 数据是模板化的（"X运营技巧/X增长秘籍"），冷门关键词会产出大量假数据污染结果。
        try:
            search_result: HotTopicSearchResult = await self.platform_api.search_hot_topics(
                keyword=keyword,
                platforms=platforms,
                days=days
            )
        except Exception as e:
            logger.warning(f"平台API调用失败: {e}，返回空结果（不再回退 mock）")
            search_result = HotTopicSearchResult(
                topics=[],
                degraded_platforms=list(platforms),
                sixty_failed_platforms=[],
                freshness="degraded",
            )

        topics = search_result.topics

        # 关键词二次过滤：兜底拦截不相关结果（标题/摘要包含关键词，大小写不敏感）
        # 例外：抖音/小红书无真实关键词搜索，0 命中时退回 TOP 榜并标为「今日热点」，
        # 这些 topic 不参与二次过滤——否则刚 fallback 进来又被这里吃掉
        kw = (keyword or "").strip().lower()
        if kw:
            topics = [
                t for t in topics
                if t.get("category") == "今日热点"
                or kw in (t.get("title") or "").lower()
                or kw in (t.get("summary") or "").lower()
                or kw in (t.get("keywords") or "").lower()
            ]

        # 按平台动态配额：总预算 10 条
        # 按所选平台数平均分配，余数顺位补给排在前的平台（按总热度降序）
        #   5 平台 → 2/2/2/2/2，3 平台 → 4/3/3，2 平台 → 5/5
        # 失败的源不进 grouped → 它的预算会被成功的源分摊（v4 精简：已无 60s 加重逻辑）
        TOTAL_BUDGET = 10
        grouped = defaultdict(list)
        for t in topics:
            source = t.get("source", "未知")
            grouped[source].append(t)

        n_sources = max(len(grouped), 1)
        base = TOTAL_BUDGET // n_sources
        remainder = TOTAL_BUDGET - base * n_sources
        sources_sorted = sorted(
            grouped.keys(),
            key=lambda s: sum(x.get("heat_value", 0) for x in grouped[s]),
            reverse=True,
        )
        quota_topics = []
        for i, source in enumerate(sources_sorted):
            items = grouped[source]
            items.sort(key=lambda x: x.get("heat_value", 0), reverse=True)
            quota = base + (1 if i < remainder else 0)
            quota_topics.extend(items[:quota])

        topics = quota_topics

        # 注入稳定 id（hash(source|title)），前端可作为 hot_topic_id 关联内容库
        import hashlib
        for t in topics:
            if not t.get("id"):
                key = f"{t.get('source','')}|{t.get('title','')}"
                t["id"] = hashlib.md5(key.encode("utf-8")).hexdigest()[:16]

        hot_topics = [HotTopicResponse(**t) for t in topics]

        from datetime import datetime
        cached_at_dt = None
        if search_result.cached_at:
            cached_at_dt = datetime.fromtimestamp(search_result.cached_at)

        return TrendingSearchResponse(
            keyword=keyword,
            total_count=len(hot_topics),
            hot_topics=hot_topics,
            degraded_platforms=search_result.degraded_platforms,
            sixty_failed_platforms=search_result.sixty_failed_platforms,
            used_cache=search_result.used_cache,
            cached_at=cached_at_dt,
            freshness=search_result.freshness,
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
