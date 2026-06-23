"""
平台数据获取服务

支持从第三方平台获取热点和对标账号数据
包括：新榜、灰豚、微博热搜等数据源
"""
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from backend.config.settings import settings

logger = logging.getLogger(__name__)

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

    async def search_hot_topics(
        self,
        keyword: str,
        platforms: List[str],
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        搜索热点话题

        Args:
            keyword: 搜索关键词
            platforms: 平台列表
            days: 搜索天数

        Returns:
            热点话题列表
        """
        results = []
        degraded: List[str] = []

        # 平台映射：前端传入 -> 内部 scraper key 列表
        # baidu 被选时同时跑 baidu+toutiao 两源（都是关键词驱动），保证关键词一定有结果
        # weibo/zhihu 走 60s 热榜过滤，冷门词可能 0 命中（这是数据源限制，非 bug）
        # douyin/xiaohongshu 0 命中时 fallback 到 TOP 热榜（见 SixtysXxxScraper.fallback_when_empty）
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
                scraper = self.scrapers[key]
                try:
                    topics = await scraper.search(keyword, days)
                    if topics:
                        results.extend(topics)
                        any_success = True
                    else:
                        logger.info(f"{platform}/{key} 关键词 [{keyword}] 无结果")
                except Exception as e:
                    logger.warning(f"{platform}/{key} 真实数据源失败: {type(e).__name__}: {e}")

            if not any_success:
                degraded.append(platform)

        if degraded:
            logger.warning(f"本次搜索 degraded 平台: {degraded}")

        # 聚合和去重
        if SCRAPERS_AVAILABLE and results:
            results = self.aggregator.aggregate(results, max_count=30)

        return results

    async def _fetch_weibo_trending(
        self,
        keyword: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """
        获取微博热搜

        注意：微博热搜需要爬虫或官方API
        这里返回模拟数据，实际使用时需接入真实API
        """
        if not self.xinbang_api_key:
            logger.info("未配置新榜API，使用mock数据")
            return self._mock_hot_topics(keyword, "weibo", days)

        # 实际实现：调用新榜API
        # try:
        #     response = await self.client.get(
        #         f"https://api.newrank.cn/hot/weibo",
        #         headers={"apikey": self.xinbang_api_key},
        #         params={"keyword": keyword, "days": days}
        #     )
        #     return response.json()
        # except httpx.HTTPStatusError as e:
        #     if e.response.status_code == 429:
        #         raise RateLimitError("微博热搜API限流")
        #     raise PlatformAPIError(f"微博热搜API错误: {e}")

        return self._mock_hot_topics(keyword, "weibo", days)

    async def _fetch_douyin_trending(
        self,
        keyword: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """获取抖音热点"""
        if not self.xinbang_api_key:
            return self._mock_hot_topics(keyword, "douyin", days)

        # 实际实现：调用新榜API
        return self._mock_hot_topics(keyword, "douyin", days)

    async def _fetch_xiaohongshu_trending(
        self,
        keyword: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """获取小红书热点"""
        if not self.xinbang_api_key:
            return self._mock_hot_topics(keyword, "xiaohongshu", days)

        # 实际实现：调用新榜API
        return self._mock_hot_topics(keyword, "xiaohongshu", days)

    def _mock_hot_topics(
        self,
        keyword: str,
        platform: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """生成模拟热点数据（小红书等暂无真实数据源时使用，URL 走真实搜索页）"""
        import random
        from urllib.parse import quote

        # 平台中文名 + 真实搜索 URL 模板
        platform_meta = {
            "weibo":       ("微博热搜", "https://s.weibo.com/weibo?q={q}"),
            "douyin":      ("抖音热榜", "https://www.douyin.com/search/{q}"),
            "xiaohongshu": ("小红书",   "https://www.xiaohongshu.com/search_result?keyword={q}"),
            "baidu":       ("百度新闻", "https://www.baidu.com/s?wd={q}&tn=news"),
            "zhihu":       ("知乎热榜", "https://www.zhihu.com/search?type=content&q={q}"),
        }
        source_name, url_tpl = platform_meta.get(platform, (platform, "https://www.google.com/search?q={q}"))

        topics = [
            f"{keyword}行业新趋势",
            f"{keyword}爆款内容分析",
            f"{keyword}怎么做",
            f"{keyword}避坑指南",
            f"{keyword}入门教程",
            f"{keyword}运营技巧",
            f"2026最新{keyword}玩法",
            f"{keyword}数据报告",
            f"{keyword}增长秘籍",
            f"关于{keyword}的真相"
        ]

        result = []
        for i, title in enumerate(topics):
            result.append({
                "title": title,
                "heat_value": random.randint(10000, 999999),
                "source": source_name,
                "trend_direction": random.choice(["up", "down", "same"]),
                "summary": f"这是关于{title}的热点摘要...",
                "source_url": url_tpl.format(q=quote(title)),
                "published_at": datetime.now() - timedelta(days=random.randint(0, days)),
                "crawled_at": datetime.now(),
                "category": "综合",
                "image_url": "",
                "keywords": keyword
            })

        return sorted(result, key=lambda x: x["heat_value"], reverse=True)


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
