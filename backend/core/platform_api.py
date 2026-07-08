"""
平台数据获取服务

支持从第三方平台获取热点和对标账号数据
包括：新榜、灰豚、微博热搜等数据源

v3 改造：60s-api 失败检测 + baidu 加重 + 失败计数器触发快速失败
"""
import time
from dataclasses import dataclass, field
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# 60s-api 失败检测阈值（连续失败次数）
SIXTYS_FAILURE_THRESHOLD = 3
# 触发快速失败的时间窗口（秒）
SIXTYS_FAST_FAIL_WINDOW = 30
# 60s 失败 ≥ 此数量 → baidu 加重
SIXTYS_BAIDU_BOOST_THRESHOLD = 2
# baidu 加重时额外抓取条数
BAIDU_BOOST_COUNT = 20


@dataclass
class HotTopicSearchResult:
    """热点搜索结果（v3 改造：携带 degraded/cached 元信息）

    Attributes:
        topics: 聚合后的热点话题列表
        degraded_platforms: 本次搜索降级的平台（前端用于黄条提示）
        sixty_failed_platforms: 60s-api 失败的具体平台
        used_cache: 是否全部命中缓存
        cached_at: 缓存命中时的写入时间（None 表示非缓存）
        freshness: fresh | stale | degraded
            - fresh: 全 60s 正常 + 新鲜数据
            - stale: 缓存命中但 TTL < 60s 即将过期
            - degraded: 有失败或降级
    """
    topics: List[Dict[str, Any]] = field(default_factory=list)
    degraded_platforms: List[str] = field(default_factory=list)
    sixty_failed_platforms: List[str] = field(default_factory=list)
    used_cache: bool = False
    cached_at: Optional[float] = None
    freshness: str = "fresh"


# 60s-api endpoint 集合（用于识别哪些失败属于 60s 而不是 baidu）
SIXTYS_ENDPOINTS = {"weibo", "zhihu", "douyin", "toutiao", "xiaohongshu"}


# 导入爬虫
try:
    from backend.scrapers.baidu_news import BaiduNewsScraper
    from backend.scrapers.weibo import WeiboScraper
    from backend.scrapers.zhihu import ZhihuScraper
    from backend.scrapers.douyin import DouyinScraper
    from backend.scrapers.xiaohongshu import XiaohongshuScraper
    from backend.scrapers.aggregator import HotTopicAggregator
    from backend.scrapers.toutiao_search import ToutiaoSearchScraper
    from backend.scrapers.sixtys import (
        SixtysWeiboScraper,
        SixtysZhihuScraper,
        SixtysDouyinScraper,
        SixtysToutiaoScraper,
        SixtysXiaohongshuScraper,
    )
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
    """热点话题API"""

    def __init__(self):
        self.xinbang_api_key = settings.XINBANG_API_KEY
        self.weibo_api_url = "https://s.weibo.com/top/summary"
        self.timeout = 30
        self.client = httpx.AsyncClient(timeout=self.timeout)

        # 60s-api 失败计数器（v3 改造）
        self._sixty_consecutive_failures: int = 0
        self._sixty_last_failure_at: Optional[float] = None

        # 初始化爬虫
        # 数据源选择原则：
        # - baidu/toutiao：真实关键词搜索，冷词也能命中
        # - weibo/zhihu：60s TOP 50 热榜，关键词命中则返回，否则空（已有 baidu 兜底）
        # - douyin/xiaohongshu：60s 热榜 + fallback_when_empty=True
        #   关键词 0 命中时退回 TOP 15 当作"今日热点"，避免这两大平台永远空
        self.scrapers = {}
        if SCRAPERS_AVAILABLE:
            self.scrapers = {
                "baidu": BaiduNewsScraper(timeout=self.timeout),
                "toutiao": ToutiaoSearchScraper(timeout=self.timeout),
                "weibo": SixtysWeiboScraper(timeout=self.timeout),
                "zhihu": SixtysZhihuScraper(timeout=self.timeout),
                "douyin": SixtysDouyinScraper(timeout=self.timeout),
                "xiaohongshu": SixtysXiaohongshuScraper(timeout=self.timeout),
            }
        self.aggregator = HotTopicAggregator() if SCRAPERS_AVAILABLE else None

    async def close(self):
        """关闭HTTP客户端和爬虫"""
        await self.client.aclose()
        for scraper in self.scrapers.values():
            await scraper.close()

    def _record_sixty_success(self) -> None:
        """60s-api 至少有一个平台成功时调用，重置计数器"""
        if self._sixty_consecutive_failures > 0:
            logger.info(f"60s-api 恢复，失败计数从 {self._sixty_consecutive_failures} 清零")
        self._sixty_consecutive_failures = 0
        self._sixty_last_failure_at = None

    def _record_sixty_failure(self) -> None:
        """60s-api 失败时调用，更新计数器"""
        self._sixty_consecutive_failures += 1
        self._sixty_last_failure_at = time.time()
        if self._sixty_consecutive_failures >= SIXTYS_FAILURE_THRESHOLD:
            logger.error(
                f"60s-api 连续 {self._sixty_consecutive_failures} 次失败，"
                f"触发快速失败（{SIXTYS_FAST_FAIL_WINDOW}s 内跳过 60s-api）"
            )

    def _should_fast_fail_sixtys(self) -> bool:
        """是否应该跳过 60s-api 调用（节省 60s × N 平台等待）"""
        if self._sixty_consecutive_failures < SIXTYS_FAILURE_THRESHOLD:
            return False
        if self._sixty_last_failure_at is None:
            return False
        return (time.time() - self._sixty_last_failure_at) < SIXTYS_FAST_FAIL_WINDOW

    async def _fetch_baidu_boost(self, keyword: str, days: int) -> List[Dict[str, Any]]:
        """baidu 加重抓取：60s 失败多时多抓 baidu 凑数（v3 改造）

        baidu 是自抓不依赖第三方，是稳定兜底。
        不写入 TTLCache（让新鲜度优先）
        """
        if not SCRAPERS_AVAILABLE:
            return []
        baidu = self.scrapers.get("baidu")
        if not baidu:
            return []
        try:
            topics = await baidu.search(keyword, days)
            return topics[:BAIDU_BOOST_COUNT]
        except Exception as e:
            logger.warning(f"baidu 加重也失败: {type(e).__name__}: {e}")
            return []

    async def search_hot_topics(
        self,
        keyword: str,
        platforms: List[str],
        days: int = 7
    ) -> HotTopicSearchResult:
        """
        搜索热点话题（v3 改造：返回 HotTopicSearchResult 含元信息）

        Args:
            keyword: 搜索关键词
            platforms: 平台列表
            days: 搜索天数

        Returns:
            HotTopicSearchResult 含 topics + degraded_platforms + freshness 等
        """
        fast_fail = self._should_fast_fail_sixtys()
        if fast_fail:
            logger.warning(
                f"60s-api 处于快速失败窗口（连续 {self._sixty_consecutive_failures} 次失败），"
                f"本次跳过 60s 直接走 baidu 加重"
            )

        results: List[Dict[str, Any]] = []
        degraded: List[str] = []
        sixty_failed: List[str] = []
        any_sixty_success = False

        # 平台映射：前端传入 -> 内部 scraper key 列表
        platform_map = {
            "baidu": ["baidu", "toutiao"],
            "weibo": ["weibo"],
            "zhihu": ["zhihu"],
            "douyin": ["douyin"],
            "toutiao": ["toutiao"],
            "xiaohongshu": ["xiaohongshu"],
        }

        for platform in platforms:
            mapped_keys = platform_map.get(platform, [platform])

            available_keys = [k for k in mapped_keys if SCRAPERS_AVAILABLE and k in self.scrapers]
            if not available_keys:
                logger.warning(f"平台 [{platform}] 暂无可用真实数据源，标记为 degraded")
                degraded.append(platform)
                continue

            any_success = False
            for key in available_keys:
                # 快速失败窗口内跳过 60s-api
                if fast_fail and key in SIXTYS_ENDPOINTS:
                    sixty_failed.append(key)
                    continue

                scraper = self.scrapers[key]
                try:
                    topics = await scraper.search(keyword, days)
                    if topics:
                        results.extend(topics)
                        any_success = True
                        if key in SIXTYS_ENDPOINTS:
                            any_sixty_success = True
                    else:
                        logger.info(f"{platform}/{key} 关键词 [{keyword}] 无结果")
                except Exception as e:
                    logger.warning(f"{platform}/{key} 真实数据源失败: {type(e).__name__}: {e}")
                    if key in SIXTYS_ENDPOINTS:
                        sixty_failed.append(key)

            if not any_success:
                degraded.append(platform)

        # 60s-api 失败 ≥2 个平台 → baidu 加重（v3 改造）
        if len(sixty_failed) >= SIXTYS_BAIDU_BOOST_THRESHOLD:
            logger.info(f"60s-api 失败 {len(sixty_failed)} 个平台 {sixty_failed}，启用 baidu 加重")
            baidu_topics = await self._fetch_baidu_boost(keyword, days)
            if baidu_topics:
                results.extend(baidu_topics)

        # 计数器更新
        if sixty_failed and any_sixty_success:
            self._record_sixty_failure()  # 部分失败，仍累计
        elif sixty_failed and not any_sixty_success:
            self._record_sixty_failure()  # 全失败
        elif any_sixty_success:
            self._record_sixty_success()  # 至少一个成功，重置

        # 聚合和去重（baidu 加重后整体聚合）
        if SCRAPERS_AVAILABLE and results:
            results = self.aggregator.aggregate(results, max_count=30)

        # 计算 freshness
        if sixty_failed or len(degraded) >= 2:
            freshness = "degraded"
        elif any_sixty_success:
            freshness = "fresh"
        else:
            freshness = "fresh"  # 全部走 baidu，不算 degraded

        if degraded or sixty_failed:
            logger.warning(
                f"本次搜索 degraded={degraded} sixty_failed={sixty_failed} freshness={freshness}"
            )

        return HotTopicSearchResult(
            topics=results,
            degraded_platforms=degraded,
            sixty_failed_platforms=sixty_failed,
            used_cache=False,  # 缓存命中在调用方（trending_service）层检测
            cached_at=None,
            freshness=freshness,
        )


class CompetitorAPI:
    """对标账号API"""

    def __init__(self):
        self.huitun_api_key = settings.HUITUN_API_KEY
        self.xinbang_api_key = settings.XINBANG_API_KEY
        self.timeout = 30
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

    async def search_competitors(
        self,
        niche: str,
        platforms: List[str],
        min_followers: int = 10000,
        max_followers: int = 1000000,
        min_avg_likes: int = 100
    ) -> List[Dict[str, Any]]:
        """
        搜索对标账号

        Args:
            niche: 赛道
            platforms: 平台列表
            min_followers: 最小粉丝数
            max_followers: 最大粉丝数
            min_avg_likes: 最小平均点赞

        Returns:
            对标账号列表
        """
        results = []

        for platform in platforms:
            if platform == "douyin":
                try:
                    accounts = await self._fetch_douyin_competitors(
                        niche, min_followers, max_followers, min_avg_likes
                    )
                    results.extend(accounts)
                except Exception as e:
                    logger.warning(f"抖音对标账号获取失败: {e}")
            elif platform == "xiaohongshu":
                try:
                    accounts = await self._fetch_xiaohongshu_competitors(
                        niche, min_followers, max_followers, min_avg_likes
                    )
                    results.extend(accounts)
                except Exception as e:
                    logger.warning(f"小红书对标账号获取失败: {e}")

        return results

    async def _fetch_douyin_competitors(
        self,
        niche: str,
        min_followers: int,
        max_followers: int,
        min_avg_likes: int
    ) -> List[Dict[str, Any]]:
        """获取抖音对标账号"""
        if not self.xinbang_api_key:
            return self._mock_competitors(niche, "douyin", min_followers, max_followers, min_avg_likes)

        # 实际实现：调用灰豚或新榜API
        return self._mock_competitors(niche, "douyin", min_followers, max_followers, min_avg_likes)

    async def _fetch_xiaohongshu_competitors(
        self,
        niche: str,
        min_followers: int,
        max_followers: int,
        min_avg_likes: int
    ) -> List[Dict[str, Any]]:
        """获取小红书对标账号"""
        if not self.huitun_api_key:
            return self._mock_competitors(niche, "xiaohongshu", min_followers, max_followers, min_avg_likes)

        # 实际实现：调用灰豚API
        return self._mock_competitors(niche, "xiaohongshu", min_followers, max_followers, min_avg_likes)

    def _mock_competitors(
        self,
        niche: str,
        platform: str,
        min_followers: int,
        max_followers: int,
        min_avg_likes: int
    ) -> List[Dict[str, Any]]:
        """生成模拟对标账号数据"""
        import random

        nicknames = [
            f"{niche}小能手",
            f"{niche}达人",
            f"{niche}研习社",
            f"{niche}学姐",
            f"{niche}学长",
            f"{niche}研究院",
            f"{niche}日记",
            f"{niche}笔记"
        ]

        result = []
        for i, nickname in enumerate(nicknames):
            followers = random.randint(min_followers, max_followers)
            video_count = random.randint(50, 500)
            total_likes = random.randint(followers * 2, followers * 20)
            avg_likes = total_likes / video_count

            if avg_likes < min_avg_likes:
                continue

            result.append({
                "account_id": f"account_{i:04d}",
                "nickname": nickname,
                "platform": platform,
                "followers": followers,
                "total_likes": total_likes,
                "video_count": video_count,
                "avg_likes": round(avg_likes, 1),
                "avg_comments": round(avg_likes * 0.05, 1),
                "profile_url": f"https://example.com/profile/{i}",
                "avatar_url": f"https://example.com/avatar/{i}.jpg",
                "signature": f"专注{niche}领域，分享实用干货！"
            })

        return sorted(result, key=lambda x: x["followers"], reverse=True)


class PlatformAPIManager:
    """平台API管理器"""

    def __init__(self):
        self.hot_topic_api = HotTopicAPI()
        self.competitor_api = CompetitorAPI()

    async def close(self):
        """关闭所有HTTP客户端"""
        await self.hot_topic_api.close()
        await self.competitor_api.close()

    def get_hot_topic_api(self) -> HotTopicAPI:
        """获取热点API实例"""
        return self.hot_topic_api

    def get_competitor_api(self) -> CompetitorAPI:
        """获取对标账号API实例"""
        return self.competitor_api


# 全局实例
_platform_api_manager: Optional[PlatformAPIManager] = None


def get_platform_api_manager() -> PlatformAPIManager:
    """获取平台API管理器单例"""
    global _platform_api_manager
    if _platform_api_manager is None:
        _platform_api_manager = PlatformAPIManager()
    return _platform_api_manager
