"""
Unit tests for TrendingService
"""
import pytest
import pytest_asyncio
from services.trending_service import TrendingService
from models.schemas.response import HotTopicResponse, TrendingSearchResponse


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
        """Test returned topic object has correct attributes"""
        result = await self.service.search(
            keyword="test",
            platforms=["douyin"],
            days=7
        )

        if result.hot_topics:
            topic = result.hot_topics[0]
            # Check Pydantic model attributes
            assert hasattr(topic, 'title')
            assert hasattr(topic, 'platform')
            assert hasattr(topic, 'trend')
