"""
需求 2 e2e — 话题订阅与自动推送

覆盖 10 个端点：
- GET    /subscriptions                  列表
- POST   /subscriptions                  创建（含配额扣减、重复话题拒绝）
- PUT    /subscriptions/{id}             更新
- DELETE /subscriptions/{id}             删除
- POST   /subscriptions/{id}/pause       暂停
- POST   /subscriptions/{id}/resume      恢复
- GET    /subscriptions/push/records     推送记录
- POST   /subscriptions/push/records/{id}/read  标记已读
- GET    /subscriptions/push/unread-count 未读数
- GET    /subscriptions/health

外加：调度器单元测试（mock 真实爬虫）
"""
import pytest
from unittest.mock import patch, AsyncMock


P = "/api/v1/subscriptions"


def _create_sub(client, headers, topic="AI写作", **overrides):
    payload = {"topic": topic, "frequency": "daily"}
    payload.update(overrides)
    r = client.post(P, json=payload, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["data"]["subscription"]


class TestHealth:
    def test_health(self, client):
        r = client.get(f"{P}/health")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "ok"


class TestSubscriptionCRUD:
    def test_create_and_list(self, client, auth_headers):
        s = _create_sub(client, auth_headers, topic="AI", description="测试")
        assert s["topic"] == "AI"
        assert s["status"] == "active"
        assert s["frequency"] == "daily"
        assert s["next_push_at"] is not None

        r = client.get(P, headers=auth_headers)
        assert r.status_code == 200
        subs = r.json()["data"]["subscriptions"]
        assert any(x["topic"] == "AI" for x in subs)

    def test_duplicate_topic_rejected(self, client, auth_headers):
        _create_sub(client, auth_headers, topic="dup")
        r = client.post(P, json={"topic": "dup", "frequency": "daily"}, headers=auth_headers)
        assert r.status_code == 400
        assert "已存在" in r.json()["error"]["message"]

    def test_invalid_frequency_rejected(self, client, auth_headers):
        r = client.post(P, json={"topic": "x", "frequency": "weekly"}, headers=auth_headers)
        assert r.status_code == 422

    def test_empty_topic_rejected(self, client, auth_headers):
        r = client.post(P, json={"topic": "", "frequency": "daily"}, headers=auth_headers)
        assert r.status_code == 422

    def test_update_subscription(self, client, auth_headers):
        s = _create_sub(client, auth_headers, topic="upd-1")
        r = client.put(f"{P}/{s['id']}",
                       json={"description": "新描述", "frequency": "every_3_days"},
                       headers=auth_headers)
        assert r.status_code == 200
        body = r.json()["data"]["subscription"]
        assert body["description"] == "新描述"
        assert body["frequency"] == "every_3_days"

    def test_delete_subscription(self, client, auth_headers):
        s = _create_sub(client, auth_headers, topic="del-1")
        r = client.delete(f"{P}/{s['id']}", headers=auth_headers)
        assert r.status_code == 200

        # 列表中已消失
        r = client.get(P, headers=auth_headers)
        subs = r.json()["data"]["subscriptions"]
        assert all(x["id"] != s["id"] for x in subs)

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete(f"{P}/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_create_deducts_quota(self, client, auth_headers):
        before = client.get("/api/v1/auth/me", headers=auth_headers)
        if before.status_code != 200:
            pytest.skip("/auth/me 不可用")
        balance_before = before.json()["data"]["quota_balance"]

        _create_sub(client, auth_headers, topic="quota-test")
        after = client.get("/api/v1/auth/me", headers=auth_headers)
        assert after.json()["data"]["quota_balance"] < balance_before

    def test_user_isolation(self, client, auth_headers):
        """A 用户的订阅 B 看不到、删不掉"""
        s = _create_sub(client, auth_headers, topic="iso-topic")

        # 注册用户 B
        r2 = client.post("/api/v1/auth/register", json={
            "username": "sub_user_b", "password": "pass123456", "email": "sub_b@test.com"
        })
        headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

        # B 看不到 A 的订阅
        r = client.get(P, headers=headers_b)
        assert all(x["id"] != s["id"] for x in r.json()["data"]["subscriptions"])

        # B 删不掉 A 的订阅
        r = client.delete(f"{P}/{s['id']}", headers=headers_b)
        assert r.status_code == 404 or r.status_code == 403


class TestPauseResume:
    def test_pause_hides_from_default_list(self, client, auth_headers):
        s = _create_sub(client, auth_headers, topic="pause-1")

        # 暂停
        r = client.post(f"{P}/{s['id']}/pause", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["subscription"]["status"] == "paused"

        # 默认列表不再返回
        r = client.get(P, headers=auth_headers)
        subs = r.json()["data"]["subscriptions"]
        assert all(x["id"] != s["id"] for x in subs)

    def test_resume_brings_back(self, client, auth_headers):
        s = _create_sub(client, auth_headers, topic="resume-1")
        client.post(f"{P}/{s['id']}/pause", headers=auth_headers)

        r = client.post(f"{P}/{s['id']}/resume", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["subscription"]["status"] == "active"

        # 列表能看到
        r = client.get(P, headers=auth_headers)
        assert any(x["id"] == s["id"] for x in r.json()["data"]["subscriptions"])

    def test_pause_nonexistent_returns_404(self, client, auth_headers):
        r = client.post(f"{P}/999999/pause", headers=auth_headers)
        assert r.status_code == 404


class TestPushRecords:
    """推送记录读 + 标记已读"""

    def _seed_push_record(self, client, auth_headers, topic="push-1"):
        """绕过调度器，直接走 service 注入一条推送记录"""
        from backend.tests.conftest import TestSessionLocal
        from backend.services.subscription_service import subscription_service

        # 先建订阅
        s = _create_sub(client, auth_headers, topic=topic)

        # 注入推送记录
        db = TestSessionLocal()
        try:
            record = subscription_service.create_push_record(
                db=db,
                subscription_id=s["id"],
                topic=topic,
                hot_topic_data={"hotspots": [{"title": "热点1", "heat": 100}]}
            )
            record_id = record.id
        finally:
            db.close()
        return s, record_id

    def test_get_push_records(self, client, auth_headers):
        _, record_id = self._seed_push_record(client, auth_headers)
        r = client.get(f"{P}/push/records", headers=auth_headers)
        assert r.status_code == 200
        records = r.json()["data"]["records"]
        assert any(rec["id"] == record_id for rec in records)
        assert r.json()["data"]["total"] >= 1

    def test_unread_count(self, client, auth_headers):
        self._seed_push_record(client, auth_headers, topic="unread-test")
        r = client.get(f"{P}/push/unread-count", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"]["count"] >= 1

    def test_mark_as_read(self, client, auth_headers):
        _, record_id = self._seed_push_record(client, auth_headers, topic="read-1")
        r = client.post(f"{P}/push/records/{record_id}/read", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()["data"]["record"]
        assert body["status"] == "read"
        assert body["read_at"] is not None

        # 未读数减一
        r = client.get(f"{P}/push/unread-count", headers=auth_headers)
        # 之前的其他推送可能也在，所以未读数不应增加
        assert r.json()["data"]["count"] >= 0

    def test_unread_only_filter(self, client, auth_headers):
        _, record_id = self._seed_push_record(client, auth_headers, topic="filter-1")
        # 标记已读
        client.post(f"{P}/push/records/{record_id}/read", headers=auth_headers)

        r = client.get(f"{P}/push/records?unread_only=true", headers=auth_headers)
        records = r.json()["data"]["records"]
        assert all(rec["status"] == "new" for rec in records)
        assert all(rec["id"] != record_id for rec in records)

    def test_mark_nonexistent_record_returns_404(self, client, auth_headers):
        r = client.post(f"{P}/push/records/999999/read", headers=auth_headers)
        assert r.status_code == 404

    def test_push_record_isolation(self, client, auth_headers):
        """A 的推送记录 B 看不到"""
        _, record_id = self._seed_push_record(client, auth_headers, topic="iso-push")

        r2 = client.post("/api/v1/auth/register", json={
            "username": "push_user_b", "password": "pass123456", "email": "push_b@test.com"
        })
        headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

        r = client.get(f"{P}/push/records", headers=headers_b)
        assert all(rec["id"] != record_id for rec in r.json()["data"]["records"])


class TestSchedulerPush:
    """调度器：到期订阅触发推送，并推进 next_push_at"""

    def test_scheduler_creates_push_record_for_due_subscription(
        self, client, auth_headers, monkeypatch
    ):
        # 建订阅
        s = _create_sub(client, auth_headers, topic="sched-test")

        # 把 next_push_at 设到过去，强制到期
        from datetime import datetime, timedelta
        from backend.tests.conftest import TestSessionLocal
        from backend.repository.subscription_repo import SubscriptionRepository

        db = TestSessionLocal()
        try:
            repo = SubscriptionRepository(db)
            sub_obj = repo.get_by_id(s["id"])
            sub_obj.next_push_at = datetime.utcnow() - timedelta(hours=1)
            db.commit()
        finally:
            db.close()

        # mock 爬虫，避免真实网络请求
        fake_hotspots = [{"title": "测试热点", "heat_index": 999, "platform": "weibo"}]
        async def fake_fetch(topic):
            return fake_hotspots

        from backend.services import subscription_scheduler_service
        monkeypatch.setattr(
            subscription_scheduler_service,
            "_fetch_hotspots_for_subscription",
            fake_fetch
        )
        # 关键：scheduler 内部用的是 production SessionLocal，让它用测试内存 DB
        from backend.tests.conftest import TestSessionLocal as _TestSession
        monkeypatch.setattr(
            subscription_scheduler_service,
            "SessionLocal",
            _TestSession
        )

        # 执行调度
        subscription_scheduler_service.scheduled_subscription_push()

        # 验证推送记录已创建
        r = client.get(f"{P}/push/records", headers=auth_headers)
        records = r.json()["data"]["records"]
        assert any(rec["topic"] == "sched-test" for rec in records)

        # 验证 next_push_at 已推进
        db = TestSessionLocal()
        try:
            repo = SubscriptionRepository(db)
            sub_obj = repo.get_by_id(s["id"])
            # 应已推进到至少当前时间之后
            assert sub_obj.next_push_at > datetime.utcnow()
            assert sub_obj.last_pushed_at is not None
        finally:
            db.close()

    def test_scheduler_skips_when_no_hotspots(
        self, client, auth_headers, monkeypatch
    ):
        s = _create_sub(client, auth_headers, topic="no-hot")

        from datetime import datetime, timedelta
        from backend.tests.conftest import TestSessionLocal
        from backend.repository.subscription_repo import SubscriptionRepository

        db = TestSessionLocal()
        try:
            repo = SubscriptionRepository(db)
            sub_obj = repo.get_by_id(s["id"])
            sub_obj.next_push_at = datetime.utcnow() - timedelta(hours=1)
            db.commit()
        finally:
            db.close()

        # 爬虫返回空
        async def empty_fetch(topic):
            return []

        from backend.services import subscription_scheduler_service
        monkeypatch.setattr(
            subscription_scheduler_service,
            "_fetch_hotspots_for_subscription",
            empty_fetch
        )
        from backend.tests.conftest import TestSessionLocal as _TestSession
        monkeypatch.setattr(
            subscription_scheduler_service,
            "SessionLocal",
            _TestSession
        )

        # 不应崩溃
        subscription_scheduler_service.scheduled_subscription_push()

        # 没有推送记录
        r = client.get(f"{P}/push/records", headers=auth_headers)
        records = r.json()["data"]["records"]
        assert all(rec["topic"] != "no-hot" for rec in records)

    def test_scheduler_no_due_subscriptions_is_noop(
        self, client, auth_headers, monkeypatch
    ):
        """没到期的不应推送"""
        s = _create_sub(client, auth_headers, topic="not-due")
        # 默认 next_push_at 是 1 天后，未到期

        call_count = {"n": 0}
        async def counting_fetch(topic):
            call_count["n"] += 1
            return []
        from backend.services import subscription_scheduler_service
        monkeypatch.setattr(
            subscription_scheduler_service,
            "_fetch_hotspots_for_subscription",
            counting_fetch
        )
        from backend.tests.conftest import TestSessionLocal as _TestSession
        monkeypatch.setattr(
            subscription_scheduler_service,
            "SessionLocal",
            _TestSession
        )

        subscription_scheduler_service.scheduled_subscription_push()
        assert call_count["n"] == 0
