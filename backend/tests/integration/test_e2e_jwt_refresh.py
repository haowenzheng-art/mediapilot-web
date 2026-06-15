"""
E2E 测试 — JWT 认证全流程
覆盖：注册/登录返回 refresh_token、刷新令牌轮转、过期 token 拒绝、类型混淆拒绝、登出、清理
"""
import pytest
from backend.core.jwt import (
    create_access_token, create_refresh_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.tests.conftest import TestSessionLocal
from datetime import timedelta


class TestRegisterReturnsTokens:
    """注册应同时返回 access_token 和 refresh_token"""

    def test_register_has_refresh_token(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "password": "test123456",
            "email": "new@test.com"
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "token" in data
        assert "refresh_token" in data
        assert len(data["token"]) > 0
        assert len(data["refresh_token"]) > 0
        assert data["token"] != data["refresh_token"]

    def test_register_token_types(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "password": "test123456",
            "email": "new@test.com"
        })
        data = resp.json()["data"]
        access_payload = decode_token(data["token"], expected_type="access")
        assert access_payload["type"] == "access"

        refresh_payload = decode_token(data["refresh_token"], expected_type="refresh")
        assert refresh_payload["type"] == "refresh"

        assert access_payload["sub"] == refresh_payload["sub"]


class TestLoginReturnsTokens:
    """登录应同时返回 access_token 和 refresh_token"""

    def test_login_has_refresh_token(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "username": "e2e_tester",
            "password": "test123456"
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "token" in data
        assert "refresh_token" in data
        assert data["token"] != data["refresh_token"]


class TestRefreshEndpoint:
    """POST /auth/refresh 端点测试"""

    def test_refresh_success(self, client, registered_user):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["refresh_token"]
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "token" in data
        assert "refresh_token" in data
        from backend.core.jwt import decode_token
        new_payload = decode_token(data["token"], expected_type="access")
        assert new_payload["sub"] == str(registered_user["user"]["id"])
        assert new_payload["type"] == "access"

        new_refresh_payload = decode_token(data["refresh_token"], expected_type="refresh")
        assert new_refresh_payload["sub"] == str(registered_user["user"]["id"])
        assert new_refresh_payload["type"] == "refresh"

    def test_refresh_returns_new_token_pair(self, client, registered_user):
        """刷新应返回可用的新 token 对"""
        import time
        time.sleep(1)

        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["refresh_token"]
        })
        assert resp.status_code == 200
        data = resp.json()["data"]

        me_resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {data['token']}"
        })
        assert me_resp.status_code == 200

    def test_refresh_with_access_token_fails(self, client, registered_user):
        """用 access_token 当 refresh_token 应失败"""
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["token"]
        })
        assert resp.status_code == 401

    def test_refresh_with_invalid_token_fails(self, client):
        """无效 refresh_token 应返回 401"""
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "garbage.token.here"
        })
        assert resp.status_code == 401

    def test_refresh_missing_field(self, client):
        """缺少 refresh_token 字段应返回 422"""
        resp = client.post("/api/v1/auth/refresh", json={})
        assert resp.status_code == 422

    def test_new_access_token_works(self, client, registered_user):
        """刷新后的 access_token 可以正常访问受保护端点"""
        refresh_resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["refresh_token"]
        })
        new_token = refresh_resp.json()["data"]["token"]

        me_resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {new_token}"
        })
        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["username"] == "e2e_tester"


class TestTokenRotation:
    """刷新令牌轮转：旧 refresh_token 使用后应被撤销"""

    def test_old_refresh_token_rejected_after_rotation(self, client, registered_user):
        """轮转后旧的 refresh_token 不能再次使用"""
        old_refresh = registered_user["refresh_token"]

        # 第一次刷新成功
        resp1 = client.post("/api/v1/auth/refresh", json={
            "refresh_token": old_refresh
        })
        assert resp1.status_code == 200

        # 用同一个旧 refresh_token 再次刷新应失败
        resp2 = client.post("/api/v1/auth/refresh", json={
            "refresh_token": old_refresh
        })
        assert resp2.status_code == 401

    def test_new_refresh_token_works_after_rotation(self, client, registered_user):
        """轮转后的新 refresh_token 可以正常使用"""
        resp1 = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["refresh_token"]
        })
        new_refresh = resp1.json()["data"]["refresh_token"]

        resp2 = client.post("/api/v1/auth/refresh", json={
            "refresh_token": new_refresh
        })
        assert resp2.status_code == 200

    def test_unregistered_refresh_token_rejected(self, client, registered_user):
        """不在 DB 中的 refresh_token 应被拒绝"""
        # 手动构造一个合法的 refresh token，但它不在 DB 中
        forged_refresh = create_refresh_token(
            data={"sub": str(registered_user["user"]["id"]), "username": "e2e_tester"}
        )
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": forged_refresh
        })
        assert resp.status_code == 401


class TestExpiredTokenRejection:
    """过期 token 应被拒绝"""

    def test_expired_access_token(self, client, registered_user):
        """手动构造已过期的 access_token 应无法访问"""
        expired_token = create_access_token(
            data={"sub": str(registered_user["user"]["id"]), "username": "e2e_tester"},
            expires_delta=timedelta(seconds=-1)
        )
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {expired_token}"
        })
        assert resp.status_code == 401

    def test_expired_refresh_token(self, client, registered_user):
        """手动构造已过期的 refresh_token 应无法刷新"""
        expired_refresh = create_refresh_token(
            data={"sub": str(registered_user["user"]["id"]), "username": "e2e_tester"},
            expires_delta=timedelta(seconds=-1)
        )
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": expired_refresh
        })
        assert resp.status_code == 401


class TestTokenTypeConfusion:
    """token 类型混淆应被拒绝"""

    def test_use_refresh_as_access(self, client, registered_user):
        """用 refresh_token 访问受保护端点应失败"""
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {registered_user['refresh_token']}"
        })
        assert resp.status_code == 401

    def test_use_access_as_refresh(self, client, registered_user):
        """用 access_token 刷新应失败"""
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["token"]
        })
        assert resp.status_code == 401


class TestLogoutEndpoint:
    """POST /auth/logout 端点测试"""

    def test_logout_revokes_refresh_token(self, client, registered_user, auth_headers):
        """登出后 refresh_token 应被撤销"""
        resp = client.post("/api/v1/auth/logout", json={
            "refresh_token": registered_user["refresh_token"]
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["revoked"] is True

        # 撤销后的 refresh_token 不能再刷新
        refresh_resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["refresh_token"]
        })
        assert refresh_resp.status_code == 401

    def test_logout_requires_auth(self, client, registered_user):
        """登出需要认证"""
        resp = client.post("/api/v1/auth/logout", json={
            "refresh_token": registered_user["refresh_token"]
        })
        assert resp.status_code == 401

    def test_logout_invalid_token(self, client, registered_user, auth_headers):
        """登出不存在的 refresh_token 应返回 400"""
        forged_refresh = create_refresh_token(
            data={"sub": str(registered_user["user"]["id"]), "username": "e2e_tester"}
        )
        resp = client.post("/api/v1/auth/logout", json={
            "refresh_token": forged_refresh
        }, headers=auth_headers)
        assert resp.status_code == 400


class TestAdminCleanupEndpoint:
    """POST /auth/admin/cleanup-tokens 端点测试"""

    @pytest.fixture
    def admin_user(self, client):
        """创建管理员用户"""
        from backend.models.database.tables import UserTable

        # 通过注册 API 创建用户
        resp = client.post("/api/v1/auth/register", json={
            "username": "admin_cleanup",
            "password": "admin123456",
            "email": "admin@test.com"
        })
        assert resp.status_code == 200

        # 使用测试 DB session 设置为管理员
        db = TestSessionLocal()
        try:
            user = db.query(UserTable).filter(UserTable.username == "admin_cleanup").first()
            user.is_admin = True
            db.commit()
        finally:
            db.close()

        # 重新登录获取新 token
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_cleanup",
            "password": "admin123456"
        })
        data = login_resp.json()["data"]
        return {
            "token": data["token"],
            "refresh_token": data["refresh_token"],
            "user": data["user"]
        }

    def test_admin_cleanup_returns_stats(self, client, admin_user):
        """管理员可以调用清理端点"""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        resp = client.post("/api/v1/auth/admin/cleanup-tokens", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "expired_deleted" in data
        assert "revoked_deleted" in data
        assert "total_deleted" in data

    def test_cleanup_forbidden_for_non_admin(self, client, registered_user, auth_headers):
        """非管理员不能调用清理端点"""
        resp = client.post("/api/v1/auth/admin/cleanup-tokens", headers=auth_headers)
        assert resp.status_code == 403


class TestProtectedEndpointsWithoutAuth:
    """未认证访问受保护端点"""

    def test_me_no_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_quota_no_token(self, client):
        resp = client.get("/api/v1/auth/quota")
        assert resp.status_code == 401

    def test_recharge_no_token(self, client):
        resp = client.post("/api/v1/auth/recharge", json={"amount": 10})
        assert resp.status_code == 401
