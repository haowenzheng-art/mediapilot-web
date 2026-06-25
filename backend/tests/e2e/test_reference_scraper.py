"""
BE-018 e2e — AI文案参考爬虫端点

不真抓网页：mock 掉 ContentReferenceScraper.get_reference_content。
只验证：
- 端点鉴权
- 参数 platforms 解析
- 返回结构 (keyword/weibo/baidu/zhihu/summary)
- 爬虫抛异常时端点不崩
"""
import pytest
from unittest.mock import AsyncMock, patch


MOCK_RESULT = {
    "keyword": "AI",
    "weibo": [{"title": "微博样例", "content": "x", "url": "https://weibo.com/x"}],
    "baidu": [{"title": "百度样例", "content": "y", "url": "https://baidu.com/y"}],
    "zhihu": [{"title": "知乎样例", "content": "z", "url": "https://zhihu.com/z"}],
    "summary": "参考摘要文本",
}


class TestReferenceContent:
    def _patch(self, return_value=None, side_effect=None):
        target = "backend.api.copywriting.ContentReferenceScraper"
        mock_scraper = AsyncMock()
        if side_effect is not None:
            mock_scraper.get_reference_content.side_effect = side_effect
        else:
            mock_scraper.get_reference_content.return_value = return_value or MOCK_RESULT
        mock_scraper.close = AsyncMock()
        return patch(target, return_value=mock_scraper)

    def test_reference_returns_full_structure(self, client, auth_headers):
        with self._patch():
            r = client.get("/api/v1/copywriting/reference",
                           params={"keyword": "AI", "platforms": "weibo,baidu,zhihu"},
                           headers=auth_headers)
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        for key in ["keyword", "weibo", "baidu", "zhihu", "summary"]:
            assert key in data
        assert data["keyword"] == "AI"
        assert isinstance(data["weibo"], list)

    def test_reference_partial_platforms(self, client, auth_headers):
        with self._patch():
            r = client.get("/api/v1/copywriting/reference",
                           params={"keyword": "测试", "platforms": "weibo"},
                           headers=auth_headers)
        assert r.status_code == 200

    def test_reference_scraper_failure_returns_500_not_crash(self, client, auth_headers):
        """爬虫抛异常应被端点捕获，返回 500 而非进程崩溃"""
        with self._patch(side_effect=RuntimeError("network blew up")):
            r = client.get("/api/v1/copywriting/reference",
                           params={"keyword": "x", "platforms": "weibo"},
                           headers=auth_headers)
        assert r.status_code == 500
        assert r.json()["success"] is False

    def test_reference_requires_auth(self, client, monkeypatch):
        from backend.config.settings import settings
        monkeypatch.setattr(settings, "DEV_MODE", False)
        r = client.get("/api/v1/copywriting/reference", params={"keyword": "x"})
        assert r.status_code == 401
