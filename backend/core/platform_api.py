"""
平台数据获取服务

支持从第三方平台获取热点数据
v4 精简：只 baidu（自抓关键词搜索）+ toutiao（自抓关键词搜索）
没有真实数据源时如实降级（degraded），绝不用 mock 假数据冒充
"""
from dataclasses import dataclass, field
import httpx
from typing import List, Dict, Optional, Any
import logging

from backend.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class HotTopicSearchResult:
    """热点搜索结果

    Attributes:
        topics: 聚合后的热点话题列表
        degraded_platforms: 本次搜索降级的平台（前端用于黄条提示）
        sixty_failed_platforms: 保留字段，前端/Schema 兼容历史契约（v4 起固定为空）
        used_cache: 是否全部命中缓存
        cached_at: 缓存命中时的写入时间（None 表示非缓存）
        freshness: fresh | stale | degraded
            - fresh: 所有源都成功
            - stale: 缓存命中但 TTL < 60s 即将过期
            - degraded: 有失败或降级
    """
    topics: List[Dict[str, Any]] = field(default_factory=list)
    degraded_platforms: List[str] = field(default_factory=list)
    sixty_failed_platforms: List[str] = field(default_factory=list)
    used_cache: bool = False
    cached_at: Optional[float] = None
    freshness: str = "fresh"


# 导入爬虫
try:
    from backend.scrapers.baidu_news import BaiduNewsScraper
    from backend.scrapers.aggregator import HotTopicAggregator
    from backend.scrapers.toutiao_search import ToutiaoSearchScraper
    SCRAPERS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"爬虫模块不可用，将使用mock数据: {e}")
    SCRAPERS_AVAILABLE = False


class PlatformAPIError(Exception):
    """平台API异常"""
    pass


class RateLimitError(PlatformAPIError):
    """限流异常"""
    pass


class HotTopicAPI:
    """热点话题API

    v4 精简：只有 baidu（自抓关键词搜索）+ toutiao（自抓关键词搜索）。
    任何源失败 → 该平台进 degraded_platforms，整体 freshness=degraded。
    """

    def __init__(self):
        self.timeout = 30
        self.client = httpx.AsyncClient(timeout=self.timeout)
        # 初始化爬虫
        self.scrapers = {}
        if SCRAPERS_AVAILABLE:
            self.scrapers = {
                "baidu": BaiduNewsScraper(timeout=self.timeout),
                "toutiao": ToutiaoSearchScraper(timeout=self.timeout),
            }
        self.aggregator = HotTopicAggregator() if SCRAPERS_AVAILABLE else None

    async def close(self):
        """关闭HTTP客户端和爬虫"""
        await self.client.aclose()
        for scraper in self.scrapers.values():
            await scraper.close()

    async def search_hot_topics(
        self,
        keyword: str,
        platforms: List[str],
        days: int = 7,
    ) -> HotTopicSearchResult:
        """搜索热点话题

        v4 简化：平台 key 1:1 对应 scraper，无映射。
        任何源抛错或返回空 → 该平台进 degraded_platforms，
        freshness 一律是 "fresh"（全部成功）或 "degraded"（任一失败/空）。
        """
        results: List[Dict[str, Any]] = []
        degraded: List[str] = []

        for platform in platforms:
            if not SCRAPERS_AVAILABLE or platform not in self.scrapers:
                logger.warning(f"平台 [{platform}] 暂无可用真实数据源，标记为 degraded")
                degraded.append(platform)
                continue

            scraper = self.scrapers[platform]
            try:
                topics = await scraper.search(keyword, days)
                if topics:
                    results.extend(topics)
                else:
                    logger.info(f"{platform} 关键词 [{keyword}] 无结果，标记 degraded")
                    degraded.append(platform)
            except Exception as e:
                logger.warning(f"{platform} 真实数据源失败: {type(e).__name__}: {e}")
                degraded.append(platform)

        # 聚合和去重
        if SCRAPERS_AVAILABLE and results:
            results = self.aggregator.aggregate(results, max_count=30)

        freshness = "degraded" if degraded else "fresh"

        if degraded:
            logger.warning(
                f"本次搜索 degraded={degraded} freshness={freshness}"
            )

        return HotTopicSearchResult(
            topics=results,
            degraded_platforms=degraded,
            sixty_failed_platforms=[],  # 保留字段，v4 起固定为空
            used_cache=False,  # 缓存命中在调用方（trending_service）层检测
            cached_at=None,
            freshness=freshness,
        )


class PlatformAPIManager:
    """平台API管理器"""

    def __init__(self):
        self.hot_topic_api = HotTopicAPI()

    async def close(self):
        """关闭所有HTTP客户端"""
        await self.hot_topic_api.close()

    def get_hot_topic_api(self) -> HotTopicAPI:
        """获取热点API实例"""
        return self.hot_topic_api


# 全局实例
_platform_api_manager: Optional[PlatformAPIManager] = None


def get_platform_api_manager() -> PlatformAPIManager:
    """获取平台API管理器单例"""
    global _platform_api_manager
    if _platform_api_manager is None:
        _platform_api_manager = PlatformAPIManager()
    return _platform_api_manager
