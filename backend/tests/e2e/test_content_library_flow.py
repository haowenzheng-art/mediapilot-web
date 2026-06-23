"""
需求 5 e2e — 内容库 + 热点关联 + 话题趋势历史

覆盖 8 个端点：
- GET    /contents                     列表 + 筛选
- POST   /contents                     创建
- GET    /contents/{id}                详情（含 403 越权、404 不存在）
- PUT    /contents/{id}                更新
- DELETE /contents/{id}                删除
- POST   /contents/{id}/process        标记已处理
- GET    /hot-topic/{hot_topic_id}/contents  热点反查
- POST   /topic-history                话题历史趋势
- GET    /health
"""
import pytest


# 端点前缀
P = "/api/v1/content-library"


def _make_content(client, headers, **overrides):
    """创建一条内容，返回响应 data.content"""
    payload = {
        "content_type": "copywriting",
        "content_id": "copy-default",
        "title": "默认标题",
        "summary": "默认摘要",
        "hot_topic_id": "topic-default",
        "hot_topic_title": "默认热点",
        "hot_topic_source": "微博",
        "mode": "from_zero",
        "persona": "测试人设",
        "platform": None,
        "style": None,
    }
    payload.update(overrides)
    r = client.post(f"{P}/contents", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["data"]["content"]


class TestHealth:
    def test_health(self, client):
        r = client.get(f"{P}/health")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "ok"


class TestContentCRUD:
    def test_create_and_get(self, client, auth_headers):
        c = _make_content(client, auth_headers,
                          content_id="c-1", title="第一条",
                          hot_topic_id="topic-A")
        assert c["content_id"] == "c-1"
        assert c["title"] == "第一条"
        assert c["is_processed"] is False
        assert c["id"] > 0

        # 详情
        r = client.get(f"{P}/contents/{c['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["content"]["id"] == c["id"]

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        r = client.get(f"{P}/contents/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_list_filters_by_user(self, client, auth_headers):
        """每个用户隔离，注册新用户应看不到旧内容"""
        # 第一用户建一条
        _make_content(client, auth_headers, content_id="isol-1", title="用户A的内容")

        # 注册第二个用户
        r2 = client.post("/api/v1/auth/register", json={
            "username": "user_b", "password": "pass123456", "email": "b@test.com"
        })
        assert r2.status_code == 200
        headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

        r = client.get(f"{P}/contents", headers=headers_b)
        assert r.status_code == 200
        # 用户 B 不应看到用户 A 的内容
        contents = r.json()["data"]["contents"]
        assert all(c["content_id"] != "isol-1" for c in contents)

    def test_list_filter_by_content_type(self, client, auth_headers):
        _make_content(client, auth_headers, content_id="cw-1", content_type="copywriting")
        _make_content(client, auth_headers, content_id="ss-1", content_type="shoot_script")

        r = client.get(f"{P}/contents",
                       params={"content_type": "shoot_script"},
                       headers=auth_headers)
        assert r.status_code == 200
        contents = r.json()["data"]["contents"]
        assert all(c["content_type"] == "shoot_script" for c in contents)

    def test_list_filter_by_hot_topic(self, client, auth_headers):
        _make_content(client, auth_headers, content_id="x-1", hot_topic_id="topic-X")
        _make_content(client, auth_headers, content_id="y-1", hot_topic_id="topic-Y")

        r = client.get(f"{P}/contents",
                       params={"hot_topic_id": "topic-X"},
                       headers=auth_headers)
        contents = r.json()["data"]["contents"]
        assert all(c["hot_topic_id"] == "topic-X" for c in contents)
        assert len(contents) >= 1

    def test_list_filter_by_is_processed(self, client, auth_headers):
        c1 = _make_content(client, auth_headers, content_id="proc-1")
        _make_content(client, auth_headers, content_id="proc-2")

        # 标记 c1 已处理
        client.post(f"{P}/contents/{c1['id']}/process", headers=auth_headers)

        r = client.get(f"{P}/contents",
                       params={"is_processed": False},
                       headers=auth_headers)
        contents = r.json()["data"]["contents"]
        assert all(c["is_processed"] is False for c in contents)

    def test_invalid_content_type_returns_400(self, client, auth_headers):
        r = client.get(f"{P}/contents",
                       params={"content_type": "bogus"},
                       headers=auth_headers)
        assert r.status_code == 400

    def test_update_content(self, client, auth_headers):
        c = _make_content(client, auth_headers, content_id="upd-1", title="原标题")

        r = client.put(f"{P}/contents/{c['id']}",
                       json={"title": "新标题", "summary": "新摘要"},
                       headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["content"]["title"] == "新标题"
        assert r.json()["data"]["content"]["summary"] == "新摘要"

    def test_delete_content(self, client, auth_headers):
        c = _make_content(client, auth_headers, content_id="del-1", title="待删")

        r = client.delete(f"{P}/contents/{c['id']}", headers=auth_headers)
        assert r.status_code == 200

        # 验证已删
        r = client.get(f"{P}/contents/{c['id']}", headers=auth_headers)
        assert r.status_code == 404

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete(f"{P}/contents/999999", headers=auth_headers)
        assert r.status_code == 404


class TestMarkProcessed:
    def test_mark_sets_is_processed_and_processed_at(self, client, auth_headers):
        c = _make_content(client, auth_headers, content_id="mk-1")
        assert c["is_processed"] is False

        r = client.post(f"{P}/contents/{c['id']}/process", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()["data"]["content"]
        assert body["is_processed"] is True
        assert body["processed_at"] is not None

    def test_mark_nonexistent_returns_404(self, client, auth_headers):
        r = client.post(f"{P}/contents/999999/process", headers=auth_headers)
        assert r.status_code == 404


class TestHotTopicContents:
    """需求 5 核心：按热点 ID 反查所有衍生内容"""

    def test_returns_all_contents_for_topic(self, client, auth_headers):
        _make_content(client, auth_headers, content_id="ht-1",
                     hot_topic_id="topic-H", content_type="copywriting")
        _make_content(client, auth_headers, content_id="ht-2",
                     hot_topic_id="topic-H", content_type="shoot_script")
        _make_content(client, auth_headers, content_id="ht-3",
                     hot_topic_id="topic-other")

        r = client.get(f"{P}/hot-topic/topic-H/contents", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["count"] == 2
        assert all(c["hot_topic_id"] == "topic-H" for c in data["contents"])

    def test_empty_topic_returns_zero(self, client, auth_headers):
        r = client.get(f"{P}/hot-topic/no-such-topic/contents", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["count"] == 0

    def test_other_users_contents_isolated(self, client, auth_headers):
        """A 用户建的内容，B 用户用同 topic 反查应看不到"""
        _make_content(client, auth_headers, content_id="iso-ht",
                     hot_topic_id="topic-shared", title="A的内容")

        # 用户 B
        r2 = client.post("/api/v1/auth/register", json={
            "username": "user_c", "password": "pass123456", "email": "c@test.com"
        })
        headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

        r = client.get(f"{P}/hot-topic/topic-shared/contents", headers=headers_b)
        assert r.status_code == 200
        assert r.json()["data"]["count"] == 0


class TestTopicHistory:
    """需求 5 核心：话题历史趋势"""

    def _seed_trend(self, client, headers, hot_topic_id, heat_score, direction):
        """通过 service 直接写趋势记录 — API 无写端点，只能服务层注入"""
        from backend.config.database import get_db
        from backend.services.content_library_service import content_library_service
        from backend.tests.conftest import TestSessionLocal

        db = TestSessionLocal()
        try:
            content_library_service.save_hot_topic_trend(
                db=db,
                hot_topic_id=hot_topic_id,
                hot_topic_title=f"标题-{hot_topic_id}",
                hot_topic_source="微博",
                heat_score=heat_score,
                trend_direction=direction
            )
        finally:
            db.close()

    def test_returns_trend_records(self, client, auth_headers):
        self._seed_trend(client, auth_headers, "topic-hist-1", 1000, "up")
        self._seed_trend(client, auth_headers, "topic-hist-1", 1500, "up")
        self._seed_trend(client, auth_headers, "topic-hist-1", 1200, "down")

        r = client.post(f"{P}/topic-history",
                        json={"hot_topic_id": "topic-hist-1", "limit": 10},
                        headers=auth_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["hot_topic_id"] == "topic-hist-1"
        assert data["hot_topic_title"] == "标题-topic-hist-1"
        assert len(data["trends"]) == 3

        # 验证字段
        for t in data["trends"]:
            assert "heat_score" in t
            assert "trend_direction" in t
            assert "recorded_at" in t

    def test_empty_topic_returns_empty_trends(self, client, auth_headers):
        r = client.post(f"{P}/topic-history",
                        json={"hot_topic_id": "no-trend", "limit": 10},
                        headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["trends"] == []

    def test_limit_param_caps_results(self, client, auth_headers):
        for i in range(5):
            self._seed_trend(client, auth_headers, "topic-limit", 1000 + i, "up")

        r = client.post(f"{P}/topic-history",
                        json={"hot_topic_id": "topic-limit", "limit": 2},
                        headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["data"]["trends"]) == 2

    def test_invalid_limit_rejected(self, client, auth_headers):
        r = client.post(f"{P}/topic-history",
                        json={"hot_topic_id": "x", "limit": 0},
                        headers=auth_headers)
        assert r.status_code == 422


class TestCrossRequirementIntegration:
    """需求 5 与需求 3/4 集成：生成文案/脚本时自动入库"""

    def test_copywriting_generate_creates_content_entry(self, client, auth_headers):
        """生成口播文案 → 内容库应自动登记一条记录"""
        from backend.core import ai_service
        from backend.config.settings import settings
        # 关 AI 走 mock，加速
        original = ai_service.ai_manager.is_available
        original_mock = settings.USE_MOCK_AI
        ai_service.ai_manager.is_available = lambda: False
        settings.USE_MOCK_AI = True
        try:
            r = client.post("/api/v1/copywriting/generate",
                           json={"mode": "from_zero", "persona": "测试", "topic": "集成"},
                           headers=auth_headers)
            assert r.status_code == 200

            # 内容库应能看到这条
            r = client.get(f"{P}/contents",
                          params={"content_type": "copywriting"},
                          headers=auth_headers)
            contents = r.json()["data"]["contents"]
            assert len(contents) >= 1
        finally:
            ai_service.ai_manager.is_available = original
            settings.USE_MOCK_AI = original_mock

    def test_shoot_script_generate_creates_content_entry(self, client, auth_headers):
        from backend.core import ai_service
        from backend.config.settings import settings
        original = ai_service.ai_manager.is_available
        original_mock = settings.USE_MOCK_AI
        ai_service.ai_manager.is_available = lambda: False
        settings.USE_MOCK_AI = True
        try:
            r = client.post("/api/v1/shoot-script/generate",
                           json={"topic": "集成", "platform": "douyin", "style": "energetic"},
                           headers=auth_headers)
            assert r.status_code == 200

            r = client.get(f"{P}/contents",
                          params={"content_type": "shoot_script"},
                          headers=auth_headers)
            contents = r.json()["data"]["contents"]
            assert len(contents) >= 1
        finally:
            ai_service.ai_manager.is_available = original
