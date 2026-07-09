"""
平台API模块单元测试

测试热点数据获取功能（v4 精简：CompetitorAPI 已下线）
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.core.platform_api import (
    HotTopicAPI,
    PlatformAPIManager,
    get_platform_api_manager,
    PlatformAPIError,
    RateLimitError,
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
        api.scrapers = {"baidu": _fake_scraper([
            _fake_topic("AI 大模型爆发", "百度新闻", 90000),
        ])}

        result = await api.search_hot_topics(keyword="AI", platforms=["baidu"], days=7)

        topics = result.topics
        assert len(topics) == 1
        assert topics[0]["title"] == "AI 大模型爆发"
        assert topics[0]["source"] == "百度新闻"
        assert topics[0]["heat_value"] == 90000
        assert result.degraded_platforms == []

    @pytest.mark.asyncio
    async def test_search_hot_topics_degraded_when_no_source(self, api):
        """核心原则：没有真实数据源时如实降级，topics 为空，绝不塞假数据"""
        api.scrapers = {}

        result = await api.search_hot_topics(keyword="AI", platforms=["baidu"], days=7)

        assert result.topics == []
        assert "baidu" in result.degraded_platforms

    @pytest.mark.asyncio
    async def test_search_hot_topics_multiple_platforms(self, api):
        """多平台：各自 scraper 有数据时都进入结果（v4 精简：baidu + toutiao）"""
        api.scrapers = {
            "baidu": _fake_scraper([_fake_topic("百度热点", "百度新闻", 50000)]),
            "toutiao": _fake_scraper([_fake_topic("头条热点", "今日头条", 40000)]),
        }

        result = await api.search_hot_topics(
            keyword="科技", platforms=["baidu", "toutiao"], days=3
        )

        sources = [t["source"] for t in result.topics]
        assert "百度新闻" in sources
        assert "今日头条" in sources
        assert result.degraded_platforms == []

    @pytest.mark.asyncio
    async def test_search_hot_topics_empty_keyword(self, api):
        """测试空关键词：返回结果对象（topics 可能为空列表）"""
        api.scrapers = {}
        result = await api.search_hot_topics(keyword="", platforms=["baidu"], days=7)

        assert hasattr(result, "topics")
        assert isinstance(result.topics, list)

    @pytest.mark.asyncio
    async def test_search_hot_topics_sorted(self, api):
        """测试结果按热度（heat_value）降序排列"""
        api.scrapers = {"baidu": _fake_scraper([
            _fake_topic("低热度", "百度新闻", 100),
            _fake_topic("高热度", "百度新闻", 99999),
            _fake_topic("中热度", "百度新闻", 5000),
        ])}

        result = await api.search_hot_topics(keyword="排序", platforms=["baidu"], days=7)

        topics = result.topics
        for i in range(1, len(topics)):
            assert topics[i - 1]["heat_value"] >= topics[i]["heat_value"]


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
