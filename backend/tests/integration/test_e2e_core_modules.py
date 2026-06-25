"""
E2E 测试 — 四大核心模块
热点搜索、脚本生成、对标账号、数据分析
验证接口可用性和响应格式
"""
from unittest.mock import patch


class TestTrendingModule:
    """热点搜索模块"""

    def test_search(self, client, auth_headers):
        resp = client.post("/api/v1/trending/search", json={
            "keyword": "AI",
            "platforms": ["douyin"],
            "days": 7
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "data" in body

    def test_search_without_auth(self, client, monkeypatch):
        """未认证访问应 401（需临时关闭测试环境的 DEV_MODE）"""
        from backend.config.settings import settings
        monkeypatch.setattr(settings, "DEV_MODE", False)
        resp = client.post("/api/v1/trending/search", json={
            "keyword": "AI",
            "platforms": ["douyin"],
            "days": 7
        })
        assert resp.status_code == 401

    def test_platforms_list(self, client):
        resp = client.get("/api/v1/trending/platforms")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    def test_health(self, client):
        resp = client.get("/api/v1/trending/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True


class TestContentModule:
    """脚本生成模块"""

    def test_generate_with_ai_mock(self, client):
        """使用 mock AI 生成脚本"""
        mock_script = {
            "script": [
                {"scene": 1, "duration": "0:00-0:05", "visual": "开场", "audio": "测试", "notes": "吸引"},
            ],
            "copywriting": {
                "title": "测试",
                "hooks": ["钩子1"],
                "call_to_action": "行动号召",
                "tags": ["测试"],
            }
        }
        with patch("backend.api.content.ai_manager") as mock_ai:
            mock_ai.is_available.return_value = True
            mock_ai.generate_content_script.return_value = mock_script

            resp = client.post("/api/v1/content/generate", json={
                "topic": "Python入门",
                "platform": "douyin",
                "duration": 60,
                "style": "professional"
            })
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            data = body["data"]
            assert "script" in data
            assert "copywriting" in data

    def test_generate_fallback_to_mock(self, client):
        """AI 不可用时使用内置 mock 数据"""
        with patch("backend.api.content.ai_manager") as mock_ai:
            mock_ai.is_available.return_value = False

            resp = client.post("/api/v1/content/generate", json={
                "topic": "测试主题"
            })
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            assert "script" in body["data"]
            assert "copywriting" in body["data"]

    def test_rewrite(self, client):
        resp = client.post("/api/v1/content/rewrite", json={
            "transcript": "这是一段测试文案用于改写验证",
            "style": "简洁"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True


class TestCompetitorsModule:
    """对标账号模块"""

    def test_search(self, client, auth_headers):
        resp = client.post("/api/v1/competitors/search", json={
            "niche": "美妆博主",
            "platforms": ["douyin", "xiaohongshu"]
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "data" in body

    def test_search_without_auth(self, client):
        resp = client.post("/api/v1/competitors/search", json={
            "niche": "美妆博主",
        })
        assert resp.status_code == 401

    def test_health(self, client):
        resp = client.get("/api/v1/competitors/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True


class TestVideoModule:
    """视频分析模块"""

    def test_fetch_video(self, client):
        resp = client.post("/api/v1/video/fetch", json={
            "url": "https://www.douyin.com/video/test"
        })
        assert resp.status_code in [200, 400, 422]

    def test_transcript(self, client):
        resp = client.post("/api/v1/video/transcript", json={
            "url": "https://www.douyin.com/video/test"
        })
        assert resp.status_code in [200, 400, 422]


class TestCalendarModule:
    """日历管理模块（需要认证）"""

    def test_create_event(self, client, auth_headers):
        resp = client.post("/api/v1/calendar/events", json={
            "title": "测试事件",
            "content": "测试内容",
            "scheduled_date": "2026-05-01",
            "platform": "douyin"
        }, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["title"] == "测试事件"

    def test_list_events(self, client, auth_headers):
        # 先创建
        client.post("/api/v1/calendar/events", json={
            "title": "测试事件",
            "content": "测试内容",
            "scheduled_date": "2026-05-01",
            "platform": "douyin"
        }, headers=auth_headers)
        # 再查询
        resp = client.get("/api/v1/calendar/events", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        # paginated_response 格式有 data + meta
        assert "data" in body

    def test_unauthorized_access(self, client):
        resp = client.get("/api/v1/calendar/events")
        assert resp.status_code == 401


class TestSystemEndpoints:
    """系统端点"""

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
