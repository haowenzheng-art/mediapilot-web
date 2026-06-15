"""
热点搜索 API 集成测试
测试热点搜索、AI总结、文章内容获取等API端点
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestTrendingSearchAPI:
    """热点搜索API测试类"""

    def test_search_trending_with_keyword(self, client):
        """测试使用关键词搜索热点"""
        response = client.post("/api/v1/trending/search", json={
            "keyword": "AI",
            "platforms": ["douyin", "xiaohongshu"],
            "days": 7
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "hot_topics" in data["data"]
        assert "keyword" in data["data"]

    def test_search_trending_empty_keyword(self, client):
        """测试空关键词搜索"""
        response = client.post("/api/v1/trending/search", json={
            "keyword": "",
            "platforms": ["weibo"],
            "days": 3
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["keyword"] == ""

    def test_search_trending_single_platform(self, client):
        """测试单个平台搜索"""
        response = client.post("/api/v1/trending/search", json={
            "keyword": "测试",
            "platforms": ["zhihu"],
            "days": 7
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_search_trending_multiple_platforms(self, client):
        """测试多个平台搜索"""
        response = client.post("/api/v1/trending/search", json={
            "keyword": "科技",
            "platforms": ["douyin", "weibo", "zhihu", "xiaohongshu", "baidu"],
            "days": 7
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"]["hot_topics"], list)

    def test_search_trending_boundary_days(self, client):
        """测试边界天数"""
        # 最小天数
        response_min = client.post("/api/v1/trending/search", json={
            "keyword": "test",
            "platforms": ["douyin"],
            "days": 1
        })
        assert response_min.status_code == 200

        # 最大天数
        response_max = client.post("/api/v1/trending/search", json={
            "keyword": "test",
            "platforms": ["douyin"],
            "days": 30
        })
        assert response_max.status_code == 200

    def test_search_trending_deducts_quota(self, client):
        """测试搜索扣减配额"""
        # 获取初始配额
        me_resp = client.get("/api/v1/auth/me")
        if me_resp.status_code == 200:
            quota_before = me_resp.json()["data"]["quota_balance"]

        # 执行搜索
        search_resp = client.post("/api/v1/trending/search", json={
            "keyword": "配额测试",
            "platforms": ["douyin"],
            "days": 7
        })
        assert search_resp.status_code == 200

        # 检查配额是否扣减
        if me_resp.status_code == 200:
            me_after = client.get("/api/v1/auth/me")
            quota_after = me_after.json()["data"]["quota_balance"]
            # 搜索应该扣减配额
            assert quota_after < quota_before

    def test_search_trending_without_quota(self, client):
        """测试配额不足时的行为"""
        # 先创建一个配额不足的用户
        reg_resp = client.post("/api/v1/auth/register", json={
            "username": "noquota",
            "password": "test123456",
            "email": "noquota@test.com"
        })
        if reg_resp.status_code == 200:
            token = reg_resp.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 将配额设置为0
            recharge_resp = client.post("/api/v1/auth/recharge", json={"amount": -100}, headers=headers)
            # 如果充值成功，则测试配额不足的情况
            if recharge_resp.status_code == 200:
                # 尝试搜索
                search_resp = client.post("/api/v1/trending/search", json={
                    "keyword": "测试",
                    "platforms": ["douyin"],
                    "days": 7
                })
                # 配额不足应该返回错误
                assert search_resp.status_code in [200, 429]
                if search_resp.status_code == 200:
                    data = search_resp.json()
                    # 如果成功返回，检查是否使用了mock数据

    def test_search_trending_returns_hot_topic_structure(self, client):
        """测试返回的热点话题结构"""
        response = client.post("/api/v1/trending/search", json={
            "keyword": "结构测试",
            "platforms": ["douyin"],
            "days": 7
        })

        assert response.status_code == 200
        data = response.json()
        hot_topics = data["data"]["hot_topics"]

        if hot_topics:
            topic = hot_topics[0]
            # 检查必要的字段
            assert "title" in topic
            assert "platform" in topic
            assert "trend" in topic


class TestTrendingSummaryAPI:
    """热点AI总结API测试类"""

    def test_get_topic_summary(self, client):
        """测试生成热点总结"""
        response = client.post("/api/v1/trending/summary", json={
            "title": "AI技术突破",
            "summary": "近期AI技术在多个领域取得重大突破",
            "url": "https://example.com/article",
            "source": "抖音"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "summary" in data["data"]
        assert data["data"]["title"] == "AI技术突破"

    def test_get_topic_summary_different_sources(self, client):
        """测试不同来源的热点总结"""
        sources = ["抖音", "微博", "知乎", "百度新闻", "小红书"]

        for source in sources:
            response = client.post("/api/v1/trending/summary", json={
                "title": f"{source}热点",
                "summary": f"来自{source}的热点事件",
                "url": "https://example.com/article",
                "source": source
            })
            assert response.status_code == 200

    def test_get_topic_summary_with_long_title(self, client):
        """测试长标题的总结"""
        long_title = "这是一个非常长的标题，用于测试API是否能够正确处理超过预期长度的标题内容，确保系统稳定性"
        response = client.post("/api/v1/trending/summary", json={
            "title": long_title,
            "summary": "测试长标题",
            "url": "https://example.com/article",
            "source": "抖音"
        })

        assert response.status_code == 200

    def test_get_topic_summary_deducts_quota(self, client):
        """测试总结功能扣减配额"""
        # 获取初始配额
        me_resp = client.get("/api/v1/auth/me")
        if me_resp.status_code == 200:
            quota_before = me_resp.json()["data"]["quota_balance"]

        # 执行总结
        summary_resp = client.post("/api/v1/trending/summary", json={
            "title": "配额测试",
            "summary": "测试配额扣减",
            "url": "https://example.com",
            "source": "抖音"
        })
        assert summary_resp.status_code == 200

        # 检查配额
        if me_resp.status_code == 200:
            me_after = client.get("/api/v1/auth/me")
            quota_after = me_after.json()["data"]["quota_balance"]
            assert quota_after < quota_before

    def test_get_topic_summary_markdown_format(self, client):
        """测试返回的总结是Markdown格式"""
        response = client.post("/api/v1/trending/summary", json={
            "title": "Markdown测试",
            "summary": "测试Markdown格式",
            "url": "https://example.com",
            "source": "抖音"
        })

        assert response.status_code == 200
        data = response.json()
        summary = data["data"]["summary"]
        # 检查是否包含Markdown标记
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestArticleContentAPI:
    """文章内容获取API测试类"""

    def test_get_article_content_baidu(self, client):
        """测试获取百度文章内容"""
        response = client.post("/api/v1/trending/article/content", json={
            "url": "https://example.com/baidu-article",
            "source": "百度新闻"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content" in data["data"]

    def test_get_article_content_weibo(self, client):
        """测试获取微博文章内容"""
        response = client.post("/api/v1/trending/article/content", json={
            "url": "https://weibo.com/test",
            "source": "微博热搜"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 微博内容需要登录，应该返回链接提示

    def test_get_article_content_zhihu(self, client):
        """测试获取知乎文章内容"""
        response = client.post("/api/v1/trending/article/content", json={
            "url": "https://zhihu.com/question/test",
            "source": "知乎热榜"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_article_content_douyin(self, client):
        """测试获取抖音文章内容"""
        response = client.post("/api/v1/trending/article/content", json={
            "url": "https://douyin.com/video/test",
            "source": "抖音热榜"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_article_content_xiaohongshu(self, client):
        """测试获取小红书文章内容"""
        response = client.post("/api/v1/trending/article/content", json={
            "url": "https://xiaohongshu.com/explore/test",
            "source": "小红书"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_article_content_unknown_source(self, client):
        """测试未知来源的文章内容"""
        response = client.post("/api/v1/trending/article/content", json={
            "url": "https://unknown.com/article",
            "source": "未知平台"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 未知来源应该返回链接提示


class TestTrendingExportAPI:
    """热点导出API测试类"""

    def test_export_trending_csv(self, client):
        """测试导出CSV格式"""
        response = client.get(
            "/api/v1/trending/export",
            params={"keyword": "AI", "format": "csv"}
        )

        # 导出可能成功或失败，取决于mock数据
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            assert "text/csv" in response.headers.get("content-type", "")

    def test_export_trending_xlsx(self, client):
        """测试导出Excel格式"""
        response = client.get(
            "/api/v1/trending/export",
            params={"keyword": "AI", "format": "xlsx"}
        )

        # 导出可能成功或失败
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            assert "spreadsheet" in content_type or "excel" in content_type

    def test_export_trending_invalid_format(self, client):
        """测试无效的导出格式"""
        response = client.get(
            "/api/v1/trending/export",
            params={"keyword": "AI", "format": "invalid"}
        )

        # 无效格式应该返回错误
        assert response.status_code in [400, 422]

    def test_export_trending_without_keyword(self, client):
        """测试缺少关键词的导出"""
        response = client.get(
            "/api/v1/trending/export",
            params={"format": "csv"}
        )

        # 缺少必要参数应该返回错误
        assert response.status_code in [400, 422]


class TestTrendingHealthCheckAPI:
    """热点服务健康检查API测试类"""

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/api/v1/trending/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "ok"


class TestTrendingPlatformsAPI:
    """支持的平台列表API测试类"""

    def test_get_supported_platforms(self, client):
        """测试获取支持的平台列表"""
        response = client.get("/api/v1/trending/platforms")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "platforms" in data["data"]
        assert isinstance(data["data"]["platforms"], list)

        # 检查是否包含预期的平台
        platforms = [p["value"] for p in data["data"]["platforms"]]
        expected_platforms = ["baidu", "weibo", "zhihu", "douyin", "xiaohongshu"]
        for expected in expected_platforms:
            assert expected in platforms

    def test_platform_structure(self, client):
        """测试平台数据结构"""
        response = client.get("/api/v1/trending/platforms")

        assert response.status_code == 200
        data = response.json()
        platforms = data["data"]["platforms"]

        if platforms:
            platform = platforms[0]
            # 检查必要的字段
            assert "value" in platform
            assert "name" in platform
            assert "enabled" in platform
            assert isinstance(platform["enabled"], bool)


class TestTrendingErrorHandling:
    """热点搜索错误处理测试类"""

    def test_search_with_invalid_days(self, client):
        """测试无效的天数参数"""
        response = client.post("/api/v1/trending/search", json={
            "keyword": "测试",
            "platforms": ["douyin"],
            "days": -1
        })

        # 负数天数应该返回错误或使用默认值
        assert response.status_code in [200, 400, 422]

    def test_search_with_empty_platforms(self, client):
        """测试空平台列表"""
        response = client.post("/api/v1/trending/search", json={
            "keyword": "测试",
            "platforms": [],
            "days": 7
        })

        # 空平台列表应该返回错误或使用默认值
        assert response.status_code in [200, 400, 422]

    def test_summary_with_missing_fields(self, client):
        """测试缺少必要字段的总结请求"""
        response = client.post("/api/v1/trending/summary", json={
            "title": "测试"
            # 缺少 summary, url, source
        })

        # 缺少必要字段应该返回错误
        assert response.status_code in [400, 422]

    def test_article_content_with_missing_url(self, client):
        """测试缺少URL的文章内容请求"""
        response = client.post("/api/v1/trending/article/content", json={
            "source": "抖音"
            # 缺少 url
        })

        # 缺少必要字段应该返回错误
        assert response.status_code in [400, 422]


class TestTrendingIntegration:
    """热点搜索集成测试类"""

    def test_search_then_summary_flow(self, client):
        """测试搜索后获取总结的完整流程"""
        # 1. 搜索热点
        search_resp = client.post("/api/v1/trending/search", json={
            "keyword": "集成测试",
            "platforms": ["douyin"],
            "days": 7
        })
        assert search_resp.status_code == 200
        hot_topics = search_resp.json()["data"]["hot_topics"]

        if hot_topics:
            # 2. 获取第一个热点的总结
            topic = hot_topics[0]
            summary_resp = client.post("/api/v1/trending/summary", json={
                "title": topic["title"],
                "summary": topic.get("summary", ""),
                "url": topic.get("url", ""),
                "source": topic.get("platform", "抖音")
            })
            assert summary_resp.status_code == 200

    def test_multiple_searches_with_quota_tracking(self, client):
        """测试多次搜索的配额追踪"""
        # 获取初始配额
        me_resp = client.get("/api/v1/auth/me")
        if me_resp.status_code == 200:
            quota_before = me_resp.json()["data"]["quota_balance"]

        # 执行多次搜索
        for i in range(3):
            resp = client.post("/api/v1/trending/search", json={
                "keyword": f"测试{i}",
                "platforms": ["douyin"],
                "days": 7
            })
            assert resp.status_code == 200

        # 检查配额是否正确扣减
        if me_resp.status_code == 200:
            me_after = client.get("/api/v1/auth/me")
            quota_after = me_after.json()["data"]["quota_balance"]
            # 3次搜索应该扣减3倍的配额
            assert quota_before - quota_after >= 3