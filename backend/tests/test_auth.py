"""Auth API 基础测试"""
import pytest
from fastapi.testclient import TestClient


def test_register_success(client: TestClient):
    """测试注册成功"""
    resp = client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "password": "test123",
        "email": "new@test.com"
    })
    assert resp.status_code == 200
    assert resp.json()["success"]
    assert resp.json()["data"]["user"]["username"] == "newuser"


def test_login_success(client: TestClient):
    """测试登录成功"""
    client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "password": "test123",
        "email": "login@test.com"
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "loginuser",
        "password": "test123"
    })
    assert resp.status_code == 200
    assert resp.json()["success"]
    assert "token" in resp.json()["data"]


def test_login_invalid(client: TestClient):
    """测试登录失败 - 错误密码"""
    client.post("/api/v1/auth/register", json={
        "username": "wronguser",
        "password": "test123",
        "email": "wrong@test.com"
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "wronguser",
        "password": "wrongpass"
    })
    assert resp.status_code == 401
    assert not resp.json()["success"]
