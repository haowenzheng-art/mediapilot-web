"""
BE-016/017/018 e2e — 口播文案生成完整流程

覆盖：
- 人设增删查（最近 3 条 LRU）
- 文案生成 3 模式（from_zero / hotspot / rewrite）
- 文案"再改改" 3 方向（more_colloquial / add_emotion / add_opinion）
- 配额扣减
- 健康检查与参考内容（reference 走 mock 路径，避免真实抓网页）
"""
import pytest


class TestPersonaAPI:
    """人设管理 API"""

    def test_create_list_delete_persona(self, client, auth_headers):
        # 初始为空
        r = client.get("/api/v1/copywriting/personas", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["personas"] == []

        # 创建
        r = client.post("/api/v1/copywriting/personas",
                        json={"persona_description": "幽默博主"},
                        headers=auth_headers)
        assert r.status_code == 200, r.text
        pid = r.json()["data"]["persona"]["id"]

        # 列表 = 1
        r = client.get("/api/v1/copywriting/personas", headers=auth_headers)
        personas = r.json()["data"]["personas"]
        assert len(personas) == 1
        assert personas[0]["persona_description"] == "幽默博主"

        # 删除
        r = client.delete(f"/api/v1/copywriting/personas/{pid}", headers=auth_headers)
        assert r.status_code == 200

        r = client.get("/api/v1/copywriting/personas", headers=auth_headers)
        assert r.json()["data"]["personas"] == []

    def test_persona_lru_at_most_three(self, client, auth_headers):
        for desc in ["A风", "B风", "C风", "D风", "E风"]:
            r = client.post("/api/v1/copywriting/personas",
                            json={"persona_description": desc},
                            headers=auth_headers)
            assert r.status_code == 200

        r = client.get("/api/v1/copywriting/personas", headers=auth_headers)
        descs = [p["persona_description"] for p in r.json()["data"]["personas"]]
        assert len(descs) == 3
        assert set(descs) == {"C风", "D风", "E风"}


class TestCopywritingGenerate:
    """文案生成 — 三种模式"""

    def _gen(self, client, headers, **payload):
        return client.post("/api/v1/copywriting/generate", json=payload, headers=headers)

    def test_mode_from_zero(self, client, auth_headers):
        r = self._gen(client, auth_headers,
                      mode="from_zero", persona="幽默博主", topic="AI写作")
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["mode"] == "from_zero"
        assert data["title"]
        assert isinstance(data["hooks"], list) and len(data["hooks"]) >= 1
        assert data["content"]

    def test_mode_hotspot(self, client, auth_headers):
        r = self._gen(client, auth_headers,
                      mode="hotspot", persona="知识博主",
                      hotspot_content="近期 AI 视频生成爆火，多家公司发布新品")
        assert r.status_code == 200, r.text
        assert r.json()["data"]["mode"] == "hotspot"

    def test_mode_rewrite(self, client, auth_headers):
        r = self._gen(client, auth_headers,
                      mode="rewrite", persona="情感博主",
                      original_text="今天天气不错，适合出去走走，心情也变好了。")
        assert r.status_code == 200, r.text
        assert r.json()["data"]["mode"] == "rewrite"

    def test_invalid_mode_rejected(self, client, auth_headers):
        r = self._gen(client, auth_headers, mode="invalid", persona="x")
        assert r.status_code == 422

    def test_generate_deducts_quota(self, client, auth_headers):
        before = client.get("/api/v1/auth/me", headers=auth_headers)
        if before.status_code != 200:
            pytest.skip("/auth/me 不可用")
        balance_before = before.json()["data"]["quota_balance"]

        r = self._gen(client, auth_headers,
                      mode="from_zero", persona="测试人设", topic="quota测试")
        assert r.status_code == 200

        after = client.get("/api/v1/auth/me", headers=auth_headers)
        assert after.json()["data"]["quota_balance"] < balance_before

    def test_generate_records_persona_to_lru(self, client, auth_headers):
        """生成时人设应进入用户的最近列表"""
        self._gen(client, auth_headers,
                  mode="from_zero", persona="生成中记录的人设", topic="abc")
        r = client.get("/api/v1/copywriting/personas", headers=auth_headers)
        descs = [p["persona_description"] for p in r.json()["data"]["personas"]]
        assert "生成中记录的人设" in descs


class TestCopywritingRewrite:
    """文案改写（再改改） — 三个方向"""

    def _generate_one(self, client, headers):
        r = client.post("/api/v1/copywriting/generate",
                        json={"mode": "from_zero", "persona": "原始人设", "topic": "原始话题"},
                        headers=headers)
        assert r.status_code == 200, r.text
        return r.json()["data"]["id"]

    @pytest.mark.parametrize("direction", ["more_colloquial", "add_emotion", "add_opinion"])
    def test_rewrite_each_direction(self, client, auth_headers, direction):
        cid = self._generate_one(client, auth_headers)
        r = client.post("/api/v1/copywriting/rewrite",
                        json={"copywriting_id": cid, "direction": direction},
                        headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["data"]["content"]

    def test_rewrite_unknown_id_returns_404(self, client, auth_headers):
        r = client.post("/api/v1/copywriting/rewrite",
                        json={"copywriting_id": "nonexistent_id_xxx",
                              "direction": "more_colloquial"},
                        headers=auth_headers)
        assert r.status_code == 404

    def test_rewrite_invalid_direction_rejected(self, client, auth_headers):
        cid = self._generate_one(client, auth_headers)
        r = client.post("/api/v1/copywriting/rewrite",
                        json={"copywriting_id": cid, "direction": "bogus"},
                        headers=auth_headers)
        assert r.status_code == 422


class TestCopywritingMisc:
    """杂项端点"""

    def test_health(self, client):
        r = client.get("/api/v1/copywriting/health")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "ok"

    def test_unauthorized_personas_returns_401(self, client, monkeypatch):
        from backend.config.settings import settings
        monkeypatch.setattr(settings, "DEV_MODE", False)
        r = client.get("/api/v1/copywriting/personas")
        assert r.status_code == 401
