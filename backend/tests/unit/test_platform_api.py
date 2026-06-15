"""
平台API模块单元测试

测试热点和对标账号数据获取功能
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.platform_api import (
    HotTopicAPI,
    CompetitorAPI,
    PlatformAPIManager,
    get_platform_api_manager,
    PlatformAPIError,
    RateLimitError
)


class TestHotTopicAPI:
    """热点API测试"""

    @pytest.fixture
    def api(self):
        """创建API实例"""
        return HotTopicAPI()

    @pytest.mark.asyncio
    async def test_search_hot_topics_weibo(self, api):
        """测试微博热搜搜索"""
        result = await api.search_hot_topics(
            keyword="AI",
            platforms=["weibo"],
            days=7
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["platform"] == "weibo"
        assert "title" in result[0]
        assert "heat_index" in result[0]
        assert "trend" in result[0]

    @pytest.mark.asyncio
    async def test_search_hot_topics_multiple_platforms(self, api):
        """测试多平台热搜搜索"""
        result = await api.search_hot_topics(
            keyword="科技",
            platforms=["douyin", "xiaohongshu"],
            days=3
        )

        assert isinstance(result, list)
        assert len(result) > 0
        platforms = [r["platform"] for r in result]
        assert "douyin" in platforms
        assert "xiaohongshu" in platforms

    @pytest.mark.asyncio
    async def test_search_hot_topics_empty_keyword(self, api):
        """测试空关键词"""
        result = await api.search_hot_topics(
            keyword="",
            platforms=["weibo"],
            days=7
        )

        # 即使关键词为空，也应该返回mock数据
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_mock_hot_topics(self, api):
        """测试mock数据生成"""
        result = api._mock_hot_topics(
            keyword="测试",
            platform="douyin",
            days=5
        )

        assert isinstance(result, list)
        assert len(result) == 10
        for topic in result:
            assert "测试" in topic["title"]
            assert topic["platform"] == "douyin"
            assert topic["heat_index"] > 0

    @pytest.mark.asyncio
    async def test_search_hot_topics_sorted(self, api):
        """测试结果按热度降序排列"""
        result = await api.search_hot_topics(
            keyword="排序",
            platforms=["weibo"],
            days=7
        )

        for i in range(1, len(result)):
            assert result[i-1]["heat_index"] >= result[i]["heat_index"]

    @pytest.mark.asyncio
    async def test_search_hot_topics_with_api_key(self, api):
        """测试有API密钥时仍返回数据（mock模式）"""
        api.xinbang_api_key = "test_key"

        result = await api.search_hot_topics(
            keyword="测试",
            platforms=["weibo"],
            days=7
        )

        assert isinstance(result, list)
        assert len(result) > 0


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
