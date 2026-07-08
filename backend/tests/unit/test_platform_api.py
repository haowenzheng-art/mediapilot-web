"""
平台API模块单元测试

测试热点和对标账号数据获取功能
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.core.platform_api import (
    HotTopicAPI,
    CompetitorAPI,
    PlatformAPIManager,
    get_platform_api_manager,
    PlatformAPIError,
    RateLimitError
)


def _fake_topic(title: str, source: str, heat_value: float) -> dict:
    """构造一条 scraper 归一化后的热点（source/heat_value/trend_direction 契约）。

    注意：platform/heat_index/trend 是下游 HotTopicResponse 的字段，
    不属于 search_hot_topics 这一层，故此处按 scraper 真实契约断言。
    """
    return {
        "title": title,
        "summary": f"{title}的摘要",
        "source": source,
        "source_url": "https://example.com/x",
        "category": "综合",
        "heat_value": heat_value,
        "trend_direction": "up",
    }


def _fake_scraper(topics: list):
    """把网络边界打桩成返回固定 topics 的假 scraper（不碰真实 60s-api）。"""
    scraper = MagicMock()
    scraper.search = AsyncMock(return_value=topics)
    return scraper


class TestHotTopicAPI:
    """热点API测试

    v3 原则：scraper 是唯一真实数据源，没有可用源就如实降级（degraded），
    绝不用 mock 假数据冒充。以下测试把 scraper 网络边界打桩，验证真实的
    聚合 / 排序 / 降级逻辑，不依赖实时网络。
    """

    @pytest.fixture
    def api(self):
        """创建API实例"""
        return HotTopicAPI()

    @pytest.mark.asyncio
    async def test_search_hot_topics_happy_path(self, api):
        """真实数据源可用时，热点按 scraper 契约透传"""
        api.scrapers = {"weibo": _fake_scraper([
            _fake_topic("AI 大模型爆发", "微博热搜", 90000),
        ])}

        result = await api.search_hot_topics(keyword="AI", platforms=["weibo"], days=7)

        topics = result.topics
        assert len(topics) == 1
        assert topics[0]["title"] == "AI 大模型爆发"
        assert topics[0]["source"] == "微博热搜"
        assert topics[0]["heat_value"] == 90000
        assert result.degraded_platforms == []

    @pytest.mark.asyncio
    async def test_search_hot_topics_degraded_when_no_source(self, api):
        """核心原则：没有真实数据源时如实降级，topics 为空，绝不塞假数据"""
        api.scrapers = {}

        result = await api.search_hot_topics(keyword="AI", platforms=["weibo"], days=7)

        assert result.topics == []
        assert "weibo" in result.degraded_platforms

    @pytest.mark.asyncio
    async def test_search_hot_topics_multiple_platforms(self, api):
        """多平台：各自 scraper 有数据时都进入结果"""
        api.scrapers = {
            "douyin": _fake_scraper([_fake_topic("抖音热点", "抖音热榜", 50000)]),
            "xiaohongshu": _fake_scraper([_fake_topic("小红书热点", "小红书", 40000)]),
        }

        result = await api.search_hot_topics(
            keyword="科技", platforms=["douyin", "xiaohongshu"], days=3
        )

        sources = [t["source"] for t in result.topics]
        assert "抖音热榜" in sources
        assert "小红书" in sources
        assert result.degraded_platforms == []

    @pytest.mark.asyncio
    async def test_search_hot_topics_empty_keyword(self, api):
        """测试空关键词：返回结果对象（topics 可能为空列表）"""
        api.scrapers = {}
        result = await api.search_hot_topics(keyword="", platforms=["weibo"], days=7)

        assert hasattr(result, "topics")
        assert isinstance(result.topics, list)

    @pytest.mark.asyncio
    async def test_search_hot_topics_sorted(self, api):
        """测试结果按热度（heat_value）降序排列"""
        api.scrapers = {"weibo": _fake_scraper([
            _fake_topic("低热度", "微博热搜", 100),
            _fake_topic("高热度", "微博热搜", 99999),
            _fake_topic("中热度", "微博热搜", 5000),
        ])}

        result = await api.search_hot_topics(keyword="排序", platforms=["weibo"], days=7)

        topics = result.topics
        for i in range(1, len(topics)):
            assert topics[i - 1]["heat_value"] >= topics[i]["heat_value"]


class TestCompetitorAPI:
    """对标账号API测试"""

    @pytest.fixture
    def api(self):
        """创建API实例"""
        return CompetitorAPI()

    @pytest.mark.asyncio
    async def test_search_competitors_douyin(self, api):
        """测试抖音对标账号搜索"""
        result = await api.search_competitors(
            niche="美妆",
            platforms=["douyin"],
            min_followers=10000,
            max_followers=100000,
            min_avg_likes=100
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(acc["platform"] == "douyin" for acc in result)
        assert "nickname" in result[0]
        assert "followers" in result[0]
        assert "avg_likes" in result[0]

    @pytest.mark.asyncio
    async def test_search_competitors_multiple_platforms(self, api):
        """测试多平台对标账号搜索"""
        result = await api.search_competitors(
            niche="科技",
            platforms=["douyin", "xiaohongshu"],
            min_followers=50000,
            max_followers=500000,
            min_avg_likes=200
        )

        assert isinstance(result, list)
        assert len(result) > 0
        platforms = [r["platform"] for r in result]
        assert len(set(platforms)) > 0

    @pytest.mark.asyncio
    async def test_search_competitors_filters(self, api):
        """测试粉丝数和点赞数过滤"""
        min_followers = 100000
        max_followers = 500000
        min_avg_likes = 500

        result = await api.search_competitors(
            niche="测试",
            platforms=["douyin"],
            min_followers=min_followers,
            max_followers=max_followers,
            min_avg_likes=min_avg_likes
        )

        for acc in result:
            assert min_followers <= acc["followers"] <= max_followers
            assert acc["avg_likes"] >= min_avg_likes

    @pytest.mark.asyncio
    async def test_mock_competitors(self, api):
        """测试mock对标账号数据生成"""
        result = api._mock_competitors(
            niche="美食",
            platform="xiaohongshu",
            min_followers=10000,
            max_followers=100000,
            min_avg_likes=100
        )

        assert isinstance(result, list)
        for acc in result:
            assert "美食" in acc["nickname"] or "美食" in acc["signature"]
            assert acc["platform"] == "xiaohongshu"
            assert acc["followers"] > 0
            assert acc["avg_likes"] >= 100

    @pytest.mark.asyncio
    async def test_search_competitors_sorted(self, api):
        """测试结果按粉丝数降序排列"""
        result = await api.search_competitors(
            niche="排序",
            platforms=["douyin"],
            min_followers=10000,
            max_followers=100000,
            min_avg_likes=100
        )

        for i in range(1, len(result)):
            assert result[i-1]["followers"] >= result[i]["followers"]

    @pytest.mark.asyncio
    async def test_search_competitors_high_min_likes(self, api):
        """测试高平均点赞过滤（可能导致结果较少）"""
        result = await api.search_competitors(
            niche="测试",
            platforms=["douyin"],
            min_followers=10000,
            max_followers=1000000,
            min_avg_likes=10000  # 高标准
        )

        # 结果可能为空或很少
        assert isinstance(result, list)
        for acc in result:
            assert acc["avg_likes"] >= 10000


class TestPlatformAPIManager:
    """平台API管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return PlatformAPIManager()

    def test_get_hot_topic_api(self, manager):
        """测试获取热点API"""
        api = manager.get_hot_topic_api()
        assert isinstance(api, HotTopicAPI)

    def test_get_competitor_api(self, manager):
        """测试获取对标账号API"""
        api = manager.get_competitor_api()
        assert isinstance(api, CompetitorAPI)

    def test_same_instance(self, manager):
        """测试返回相同实例"""
        api1 = manager.get_hot_topic_api()
        api2 = manager.get_hot_topic_api()
        assert api1 is api2

    @pytest.mark.asyncio
    async def test_close(self, manager):
        """测试关闭客户端"""
        # 获取API实例
        manager.get_hot_topic_api()
        manager.get_competitor_api()

        # 关闭应该不报错
        await manager.close()


class TestGetPlatformAPIManager:
    """全局管理器单例测试"""

    @pytest.mark.asyncio
    async def test_singleton(self):
        """测试单例模式"""
        manager1 = get_platform_api_manager()
        manager2 = get_platform_api_manager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_persistence(self):
        """测试实例持久化"""
        manager1 = get_platform_api_manager()
        api1 = manager1.get_hot_topic_api()

        manager2 = get_platform_api_manager()
        api2 = manager2.get_hot_topic_api()

        assert api1 is api2


class TestPlatformAPIError:
    """异常类测试"""

    def test_platform_api_error(self):
        """测试平台API异常"""
        error = PlatformAPIError("Test error")
        assert str(error) == "Test error"

    def test_rate_limit_error(self):
        """测试限流异常"""
        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, PlatformAPIError)
        assert str(error) == "Rate limit exceeded"
