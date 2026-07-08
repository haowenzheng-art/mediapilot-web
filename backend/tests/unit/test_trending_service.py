"""
Unit tests for TrendingService
"""
import pytest
import pytest_asyncio
from backend.services.trending_service import TrendingService
from backend.models.schemas.response import HotTopicResponse, TrendingSearchResponse


@pytest.mark.asyncio
class TestTrendingService:
    """TrendingService test class"""

    def setup_method(self):
        """Initialize service before each test"""
        self.service = TrendingService()

    async def test_search_normal_returns_topic_list(self):
        """Test normal search returns topic list"""
        result = await self.service.search(
            keyword="AI",
            platforms=["douyin", "xiaohongshu"],
            days=7
        )

        assert result.keyword == "AI"
        assert result.total_count >= 0
        assert isinstance(result.hot_topics, list)

    async def test_search_empty_keyword_returns_mock_data(self):
        """Test empty keyword returns mock data"""
        result = await self.service.search(
            keyword="",
            platforms=["douyin"],
            days=1
        )

        assert result.keyword == ""
        # Mock service returns mock data based on keyword
        assert isinstance(result.hot_topics, list)

    async def test_search_single_platform_returns_data(self):
        """Test single platform returns data"""
        result = await self.service.search(
            keyword="test",
            platforms=["douyin"],
            days=7
        )

        assert result.keyword == "test"
        # Mock service returns mock data
        assert result.total_count >= 0
        assert isinstance(result.hot_topics, list)

    async def test_search_boundary_days_normal(self):
        """Test boundary days values"""
        # Minimum days
        result_min = await self.service.search(
            keyword="test",
            platforms=["douyin"],
            days=1
        )
        assert result_min.total_count >= 0

        # Maximum days
        result_max = await self.service.search(
            keyword="test",
            platforms=["douyin"],
            days=30
        )
        assert result_max.total_count >= 0

    async def test_search_returns_topic_attributes(self):
        """返回的 topic 暴露真实契约字段：source / heat_value / trend_direction。

        历史断言里的 platform / trend 字段从未在 HotTopicResponse 中存在，
        属测试写错。此处 mock 掉 platform_api 网络边界，保证确定性、不打实时网络。
        """
        from datetime import datetime
        from unittest.mock import AsyncMock, patch
        from backend.core.platform_api import HotTopicSearchResult

        fake = HotTopicSearchResult(
            topics=[{
                "title": "test 热点",
                "summary": "关于 test 的摘要",
                "source": "抖音热榜",
                "source_url": "https://example.com/x",
                "category": "综合",
                "heat_value": 12345,
                "trend_direction": "up",
                "published_at": datetime.now(),
                "crawled_at": datetime.now(),
                "keywords": "test",
                "image_url": "",
            }],
            degraded_platforms=[],
            sixty_failed_platforms=[],
            freshness="fresh",
        )

        with patch.object(
            self.service.platform_api, "search_hot_topics",
            new=AsyncMock(return_value=fake)
        ):
            result = await self.service.search(
                keyword="test", platforms=["douyin"], days=7
            )

        assert result.hot_topics, "mock 数据应产出至少一条热点"
        topic = result.hot_topics[0]
        assert hasattr(topic, 'title')
        assert hasattr(topic, 'source')
        assert hasattr(topic, 'heat_value')
        assert hasattr(topic, 'trend_direction')
        assert topic.source == "抖音热榜"
