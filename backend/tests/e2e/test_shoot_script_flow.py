"""
需求 4 e2e — 拍摄脚本生成完整流程

覆盖：
- POST /generate — 三平台 × 三风格 参数化
- GET /{script_id} — 命中 / 未命中
- POST /export — json / txt / csv 三格式 + 非法格式
- GET /health
- 配额扣减
"""
import pytest


@pytest.fixture(autouse=True)
def _disable_real_ai(monkeypatch):
    """关掉 AI，强制走 _mock_generate — 让 e2e 快且确定。"""
    from backend.core import ai_service
    from backend.config.settings import settings
    monkeypatch.setattr(ai_service.ai_manager, "is_available", lambda: False)
    monkeypatch.setattr(settings, "USE_MOCK_AI", True)


def _gen(client, headers, **payload):
    return client.post("/api/v1/shoot-script/generate", json=payload, headers=headers)


class TestShootScriptHealth:
    def test_health(self, client):
        r = client.get("/api/v1/shoot-script/health")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "ok"


class TestShootScriptGenerate:
    """三平台 × 三风格全覆盖"""

    @pytest.mark.parametrize("platform", ["douyin", "xiaohongshu", "bilibili"])
    @pytest.mark.parametrize("style", ["energetic", "relaxed", "professional"])
    def test_generate_each_platform_and_style(self, client, auth_headers, platform, style):
        r = _gen(client, auth_headers,
                 topic="AI写作技巧",
                 platform=platform,
                 style=style,
                 persona="干货博主")
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["platform"] == platform
        assert data["style"] == style
        assert data["title"]
        assert isinstance(data["shots"], list) and len(data["shots"]) >= 3
        assert isinstance(data["hooks"], list) and len(data["hooks"]) >= 1
        assert data["call_to_action"]
        assert isinstance(data["tags"], list)
        assert data["estimated_duration"]

    def test_shot_structure(self, client, auth_headers):
        """每个镜头应含必要字段"""
        r = _gen(client, auth_headers,
                 topic="测试", platform="douyin", style="energetic")
        shots = r.json()["data"]["shots"]
        for shot in shots:
            assert "shot_number" in shot
            assert "duration" in shot
            assert "visual_description" in shot
            assert "dialogue" in shot

    def test_invalid_platform_rejected(self, client, auth_headers):
        r = _gen(client, auth_headers, topic="x", platform="instagram", style="energetic")
        assert r.status_code == 422

    def test_invalid_style_rejected(self, client, auth_headers):
        r = _gen(client, auth_headers, topic="x", platform="douyin", style="serious")
        assert r.status_code == 422

    def test_empty_topic_rejected(self, client, auth_headers):
        r = _gen(client, auth_headers, topic="", platform="douyin", style="energetic")
        assert r.status_code == 422

    def test_generate_deducts_quota(self, client, auth_headers):
        before = client.get("/api/v1/auth/me", headers=auth_headers)
        if before.status_code != 200:
            pytest.skip("/auth/me 不可用")
        balance_before = before.json()["data"]["quota_balance"]

        r = _gen(client, auth_headers,
                 topic="quota测试", platform="douyin", style="energetic")
        assert r.status_code == 200

        after = client.get("/api/v1/auth/me", headers=auth_headers)
        assert after.json()["data"]["quota_balance"] < balance_before


class TestShootScriptGet:
    def test_get_after_generate(self, client, auth_headers):
        r = _gen(client, auth_headers,
                 topic="get测试", platform="douyin", style="energetic")
        sid = r.json()["data"]["id"]

        r = client.get(f"/api/v1/shoot-script/{sid}")
        assert r.status_code == 200
        assert r.json()["data"]["id"] == sid

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/api/v1/shoot-script/nonexistent_xxx")
        assert r.status_code == 404


class TestShootScriptExport:
    def _make_script(self, client, auth_headers):
        r = _gen(client, auth_headers,
                 topic="导出测试", platform="douyin", style="energetic")
        return r.json()["data"]["id"]

    @pytest.mark.parametrize("fmt", ["json", "txt", "csv"])
    def test_export_each_format(self, client, auth_headers, fmt):
        sid = self._make_script(client, auth_headers)
        r = client.post("/api/v1/shoot-script/export",
                        json={"script_id": sid, "format": fmt})
        assert r.status_code == 200, r.text
        assert "Content-Disposition" in r.headers
        assert f".{fmt}" in r.headers["Content-Disposition"]
        # 内容非空
        assert len(r.content) > 0

    def test_export_json_is_valid(self, client, auth_headers):
        import json
        sid = self._make_script(client, auth_headers)
        r = client.post("/api/v1/shoot-script/export",
                        json={"script_id": sid, "format": "json"})
        parsed = json.loads(r.content)
        assert parsed["id"] == sid
        assert "shots" in parsed

    def test_export_txt_contains_key_sections(self, client, auth_headers):
        sid = self._make_script(client, auth_headers)
        r = client.post("/api/v1/shoot-script/export",
                        json={"script_id": sid, "format": "txt"})
        text = r.content.decode("utf-8")
        assert "标题" in text
        assert "钩子" in text
        assert "分镜头脚本" in text

    def test_export_csv_has_headers(self, client, auth_headers):
        sid = self._make_script(client, auth_headers)
        r = client.post("/api/v1/shoot-script/export",
                        json={"script_id": sid, "format": "csv"})
        text = r.content.decode("utf-8")
        assert "镜头编号" in text
        assert "台词" in text

    def test_export_invalid_format_rejected(self, client, auth_headers):
        sid = self._make_script(client, auth_headers)
        # pattern 校验在 schema 层 → 422
        r = client.post("/api/v1/shoot-script/export",
                        json={"script_id": sid, "format": "pdf"})
        assert r.status_code == 422

    def test_export_nonexistent_returns_404(self, client):
        r = client.post("/api/v1/shoot-script/export",
                        json={"script_id": "ghost_id", "format": "json"})
        assert r.status_code == 404
