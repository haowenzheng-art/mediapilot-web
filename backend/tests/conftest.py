"""
MediaPilot 集成测试 conftest
使用内存 SQLite + StaticPool 确保同一连接共享
"""
import os

# 测试环境启用 DEV_MODE，让 ensure_dev_user 注入默认用户、绕过 JWT
# 必须在 import settings 之前生效
os.environ.setdefault("DEV_MODE", "true")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config.settings import settings
settings.DEV_MODE = True  # 兜底：若 settings 已先加载，强制覆盖

from backend.main import app
from backend.config.database import get_db
from backend.models.database.tables import Base


# 内存测试数据库 — StaticPool 共享同一连接
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def db_setup():
    """每个测试函数独立数据库"""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """FastAPI 测试客户端"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def registered_user(client):
    """注册一个测试用户，返回完整 data（含 token + refresh_token）"""
    resp = client.post("/api/v1/auth/register", json={
        "username": "e2e_tester",
        "password": "test123456",
        "email": "e2e@test.com"
    })
    assert resp.status_code == 200, f"注册失败: {resp.text}"
    data = resp.json()["data"]
    return data


@pytest.fixture
def auth_headers(registered_user):
    """带 Bearer token 的请求头"""
    return {"Authorization": f"Bearer {registered_user['token']}"}


def extract_data(resp):
    """从统一响应中提取 data，断言成功"""
    body = resp.json()
    assert body.get("success"), f"请求失败: {body}"
    return body["data"]


def extract_error(resp):
    """从统一响应中提取 error"""
    body = resp.json()
    assert not body.get("success", True), f"期望失败但成功: {body}"
    return body["error"]
