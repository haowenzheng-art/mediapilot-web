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
    from scrapers.baidu_news import BaiduNewsScraper
    from scrapers.weibo import WeiboScraper
    from scrapers.zhihu import ZhihuScraper
    from scrapers.douyin import DouyinScraper
    from scrapers.xiaohongshu import XiaohongshuScraper
    from scrapers.aggregator import HotTopicAggregator
    SCRAPERS_AVAILABLE = True
except ImportError:
    logger.warning("爬虫模块不可用，将使用mock数据")
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
        self.scrapers = {}
        if SCRAPERS_AVAILABLE:
            self.scrapers = {
                "baidu": BaiduNewsScraper(timeout=self.timeout),
                "weibo": WeiboScraper(timeout=self.timeout),
                "zhihu": ZhihuScraper(timeout=self.timeout),
                "douyin": DouyinScraper(timeout=self.timeout),
                "xiaohongshu": XiaohongshuScraper(timeout=self.timeout),
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

        # 平台映射
        platform_map = {
            "baidu": "baidu",
            "weibo": "weibo",
            "zhihu": "zhihu",
            "douyin": "douyin",
            "xiaohongshu": "xiaohongshu",
        }

        for platform in platforms:
            mapped_platform = platform_map.get(platform, platform)

            if SCRAPERS_AVAILABLE and mapped_platform in self.scrapers:
                try:
                    scraper = self.scrapers[mapped_platform]
                    topics = await scraper.search(keyword, days)
                    results.extend(topics)
                except Exception as e:
                    logger.warning(f"{platform}爬虫获取失败: {e}")
            else:
                # 回退到mock数据
                if platform == "weibo":
                    try:
                        topics = await self._fetch_weibo_trending(keyword, days)
                        results.extend(topics)
                    except Exception as e:
                        logger.warning(f"微博热搜获取失败: {e}")
                elif platform == "douyin":
                    try:
                        topics = await self._fetch_douyin_trending(keyword, days)
                        results.extend(topics)
                    except Exception as e:
                        logger.warning(f"抖音热点获取失败: {e}")
                elif platform == "xiaohongshu":
                    try:
                        topics = await self._fetch_xiaohongshu_trending(keyword, days)
                        results.extend(topics)
                    except Exception as e:
                        logger.warning(f"小红书热点获取失败: {e}")
                elif platform == "baidu":
                    results.extend(self._mock_hot_topics(keyword, "百度新闻", days))
                elif platform == "zhihu":
                    results.extend(self._mock_hot_topics(keyword, "知乎热榜", days))

        # 聚合和去重
        if SCRAPERS_AVAILABLE and results:
            results = self.aggregator.aggregate(results, max_count=10)

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
        """生成模拟热点数据"""
        import random

        # 平台中文名映射
        platform_names = {
            "weibo": "微博热搜",
            "douyin": "抖音热榜",
            "xiaohongshu": "小红书",
            "baidu": "百度新闻",
            "zhihu": "知乎热榜",
        }
        source_name = platform_names.get(platform, platform)

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
                "source_url": f"https://example.com/topic/{i}",
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
