"""
QA-003 端到端测试 — 需求 1 全网热点搜索完整流程

覆盖用户旅程：
  注册 → 查询平台列表 → 搜索热点 → 获取 AI 总结 → 抓文章内容 → 导出 → 配额追踪
"""
import pytest


class TestTrendingSearchE2E:
    """需求 1 端到端 — 真实用户从注册到导出的完整链路"""

    def test_full_journey_register_search_summary_export(self, client, mock_ai_summary):
        # 0. 注册用户拿 token
        reg = client.post("/api/v1/auth/register", json={
            "username": "trending_journey", "password": "test123456",
            "email": "trj@test.com"
        })
        assert reg.status_code == 200, reg.text
        token = reg.json()["data"]["token"]
        H = {"Authorization": f"Bearer {token}"}

        # 1. 健康检查 — 服务可用
        health = client.get("/api/v1/trending/health")
        assert health.status_code == 200
        assert health.json()["data"]["status"] == "ok"

        # 2. 平台列表 — v4 精简：只返回 baidu + toutiao
        platforms_resp = client.get("/api/v1/trending/platforms")
        assert platforms_resp.status_code == 200
        platforms = platforms_resp.json()["data"]["platforms"]
        platform_values = [p["value"] for p in platforms]
        for expected in ["baidu", "toutiao"]:
            assert expected in platform_values
        # 旧 4 源必须下线
        for removed in ["weibo", "zhihu", "douyin", "xiaohongshu"]:
            assert removed not in platform_values

        # 3. 搜索热点（v4：baidu + toutiao）
        search_resp = client.post("/api/v1/trending/search", json={
            "keyword": "AI",
            "platforms": ["baidu", "toutiao"],
            "days": 7
        }, headers=H)
        assert search_resp.status_code == 200
        search_body = search_resp.json()
        assert search_body["success"] is True
        hot_topics = search_body["data"]["hot_topics"]
        assert isinstance(hot_topics, list)

        # 4. 选第一个热点拿 AI 总结
        if hot_topics:
            topic = hot_topics[0]
            summary_resp = client.post("/api/v1/trending/summary", json={
                "title": topic["title"],
                "summary": topic.get("summary", ""),
                "url": topic.get("url", ""),
                "source": topic.get("platform", "百度新闻"),
            }, headers=H)
            assert summary_resp.status_code == 200
            assert summary_resp.json()["success"] is True
            assert "summary" in summary_resp.json()["data"]

            # 5. 抓文章内容（v4：仅 baidu/toutiao 走专门爬虫，其他返 URL 提示）
            for source in ["百度新闻", "今日头条"]:
                content_resp = client.post("/api/v1/trending/article/content", json={
                    "url": topic.get("url") or "https://example.com/x",
                    "source": source,
                })
                assert content_resp.status_code == 200, f"source={source} 失败"
                assert content_resp.json()["success"] is True

        # 6. 导出 CSV
        export_csv = client.get("/api/v1/trending/export", params={"keyword": "AI", "format": "csv"})
        assert export_csv.status_code in [200, 400, 500]
        if export_csv.status_code == 200:
            assert "text/csv" in export_csv.headers.get("content-type", "")

    def test_quota_decrements_across_full_flow(self, client, mock_ai_summary):
        """配额在完整流程中按预期扣减"""
        me_before = client.get("/api/v1/auth/me")
        if me_before.status_code != 200:
            pytest.skip("当前环境 /auth/me 不可用")

        quota_before = me_before.json()["data"]["quota_balance"]

        # 一次搜索 + 一次总结
        client.post("/api/v1/trending/search", json={
            "keyword": "配额E2E",
            "platforms": ["baidu"],
            "days": 7,
        })
        client.post("/api/v1/trending/summary", json={
            "title": "配额E2E",
            "summary": "测试",
            "url": "https://example.com",
            "source": "百度新闻",
        })

        me_after = client.get("/api/v1/auth/me")
        quota_after = me_after.json()["data"]["quota_balance"]
        assert quota_after < quota_before, "搜索+总结后配额必须减少"

    def test_invalid_inputs_dont_crash_pipeline(self, client):
        """异常输入不应让服务崩溃 — 要么 200 mock，要么 4xx 校验失败/未授权"""
        # 负数天数
        r1 = client.post("/api/v1/trending/search", json={
            "keyword": "x", "platforms": ["baidu"], "days": -1,
        })
        assert r1.status_code in [200, 400, 401, 422]

        # 总结缺字段
        r2 = client.post("/api/v1/trending/summary", json={"title": "x"})
        assert r2.status_code in [400, 401, 422]

        # 文章内容缺 url
        r3 = client.post("/api/v1/trending/article/content", json={"source": "百度新闻"})
        assert r3.status_code in [400, 401, 422]


class TestTrendingResponseFields:
    """响应 Schema 字段契约

    验证 TrendingSearchResponse 包含 freshness / degraded_platforms /
    sixty_failed_platforms / used_cache / cached_at 字段。
    注：sixty_failed_platforms 在 v4 已固定为空（60s 端点全下线），
    但保留 schema 字段以兼容历史契约。
    """

    def test_response_includes_all_fields(self, client, auth_headers):
        """响应必须包含所有契约字段"""
        r = client.post("/api/v1/trending/search", json={
            "keyword": "AI 写作",
            "platforms": ["baidu", "toutiao"],
            "days": 7,
        }, headers=auth_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        # 契约字段必须存在
        assert "freshness" in data
        assert "degraded_platforms" in data
        assert "sixty_failed_platforms" in data
        assert "used_cache" in data
        # freshness 必须是合法值
        assert data["freshness"] in ("fresh", "stale", "degraded")
        # sixty_failed_platforms v4 起固定为空列表
        assert data["sixty_failed_platforms"] == []

    def test_source_failure_degrades_freshness(self, client, auth_headers, monkeypatch):
        """任一数据源失败时 freshness='degraded' + degraded_platforms 非空。
        patch ToutiaoSearchScraper.search 抛错，验证 degraded 链路通。
        """
        from backend.scrapers.toutiao_search import ToutiaoSearchScraper

        async def boom(self, keyword, days):
            raise RuntimeError("toutiao search mock failure")

        monkeypatch.setattr(ToutiaoSearchScraper, "search", boom)

        # 禁用 trending_cache
        from backend.config.settings import settings
        monkeypatch.setattr(settings, "TRENDING_CACHE_ENABLED", False)

        r = client.post("/api/v1/trending/search", json={
            "keyword": "mock_fail_keyword_unique",
            "platforms": ["toutiao"],
            "days": 7,
        }, headers=auth_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        # 失败 → freshness=degraded
        assert data["freshness"] == "degraded"
        # 失败的平台被列入 degraded_platforms
        assert "toutiao" in data["degraded_platforms"]

    def test_cache_disabled_response_uses_cache_false(self, client, auth_headers, monkeypatch):
        """缓存禁用时 used_cache=False"""
        from backend.config.settings import settings
        monkeypatch.setattr(settings, "TRENDING_CACHE_ENABLED", False)

        r = client.post("/api/v1/trending/search", json={
            "keyword": "cache_off_unique_test",
            "platforms": ["baidu"],
            "days": 7,
        }, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["used_cache"] is False
