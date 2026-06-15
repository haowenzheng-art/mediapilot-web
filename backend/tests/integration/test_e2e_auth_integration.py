"""
E2E 测试 — 跨模块认证集成
验证认证状态贯穿多个模块的正确行为
"""
from unittest.mock import patch


class TestAuthFlowAcrossModules:
    """认证状态在各模块间的一致性"""

    def test_register_then_use_all_modules(self, client):
        """注册后应能访问所有需要认证的模块"""
        # 1. 注册
        reg = client.post("/api/v1/auth/register", json={
            "username": "flowtester",
            "password": "test123456",
            "email": "flow@test.com"
        })
        assert reg.status_code == 200
        token = reg.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 内容生成（mock AI 避免真实 API 调用）
        with patch("backend.api.content.ai_manager") as mock_ai:
            mock_ai.is_available.return_value = False
            gen = client.post("/api/v1/content/generate", json={
                "topic": "测试主题"
            }, headers=headers)
            assert gen.status_code == 200

        # 3. 日历事件（需要认证）
        cal = client.post("/api/v1/calendar/events", json={
            "title": "测试",
            "content": "内容",
            "scheduled_date": "2026-05-01",
            "platform": "douyin"
        }, headers=headers)
        assert cal.status_code == 201

        # 4. 获取配额
        quota = client.get("/api/v1/auth/quota", headers=headers)
        assert quota.status_code == 200
        assert quota.json()["data"]["balance"] == 100

    def test_refresh_then_use_protected_endpoint(self, client):
        """刷新 token 后应能继续访问受保护端点"""
        # 注册
        reg = client.post("/api/v1/auth/register", json={
            "username": "refresher",
            "password": "test123456",
            "email": "refresh@test.com"
        })
        data = reg.json()["data"]

        # 刷新
        refresh = client.post("/api/v1/auth/refresh", json={
            "refresh_token": data["refresh_token"]
        })
        assert refresh.status_code == 200
        new_token = refresh.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {new_token}"}

        # 用新 token 访问
        me = client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["data"]["username"] == "refresher"

        # 日历也行
        cal = client.get("/api/v1/calendar/events", headers=headers)
        assert cal.status_code == 200

    def test_expired_token_denied_everywhere(self, client):
        """过期 token 应被所有受保护端点拒绝"""
        from backend.core.jwt import create_access_token
        from datetime import timedelta

        expired = create_access_token(
            data={"sub": "999", "username": "ghost"},
            expires_delta=timedelta(seconds=-1)
        )
        headers = {"Authorization": f"Bearer {expired}"}

        # /auth/me
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
        # /auth/quota
        assert client.get("/api/v1/auth/quota", headers=headers).status_code == 401
        # /calendar/events
        assert client.get("/api/v1/calendar/events", headers=headers).status_code == 401
        # /auth/recharge
        assert client.post("/api/v1/auth/recharge", json={"amount": 10}, headers=headers).status_code == 401

    def test_no_token_denied_protected_endpoints(self, client):
        """无 token 应被所有受保护端点拒绝"""
        assert client.get("/api/v1/auth/me").status_code == 401
        assert client.get("/api/v1/auth/quota").status_code == 401
        assert client.get("/api/v1/calendar/events").status_code == 401
        assert client.post("/api/v1/auth/recharge", json={"amount": 10}).status_code == 401

    def test_invalid_token_denied(self, client):
        """伪造 token 应被拒绝"""
        headers = {"Authorization": "Bearer totally.fake.token"}
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


class TestQuotaLifecycle:
    """配额生命周期 — 注册 → 查询 → 充值 → 验证"""

    def test_full_quota_lifecycle(self, client):
        # 注册
        reg = client.post("/api/v1/auth/register", json={
            "username": "quotauser",
            "password": "test123456",
            "email": "quota@test.com"
        })
        token = reg.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 初始配额
        q1 = client.get("/api/v1/auth/quota", headers=headers)
        assert q1.json()["data"]["balance"] == 100

        # 充值
        recharge = client.post("/api/v1/auth/recharge", json={"amount": 50}, headers=headers)
        assert recharge.status_code == 200
        assert recharge.json()["data"]["balance"] == 150
        assert recharge.json()["data"]["added"] == 50

        # 再次查询确认
        q2 = client.get("/api/v1/auth/quota", headers=headers)
        assert q2.json()["data"]["balance"] == 150

    def test_recharge_invalid_amount(self, client, auth_headers):
        """非法充值金额"""
        # 0
        r1 = client.post("/api/v1/auth/recharge", json={"amount": 0}, headers=auth_headers)
        assert r1.status_code == 400

        # 超过上限
        r2 = client.post("/api/v1/auth/recharge", json={"amount": 20000}, headers=auth_headers)
        assert r2.status_code == 400

        # 负数
        r3 = client.post("/api/v1/auth/recharge", json={"amount": -10}, headers=auth_headers)
        assert r3.status_code == 400
