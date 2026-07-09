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

    # 后台异步任务（如 media 转写）自建 SessionLocal()，绕过了 get_db override，
    # 默认写向生产库文件，导致 TestClient 用的内存库永远读不到任务结果。
    # 把这些模块级 SessionLocal 重定向到测试引擎，保证 bg 任务与请求共享同一库。
    import backend.services.media_service as _media_mod
    _orig_media_session = _media_mod.SessionLocal
    _media_mod.SessionLocal = TestSessionLocal

    yield

    _media_mod.SessionLocal = _orig_media_session
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

# 固定 AI 总结 mock 返回值：符合 v2 prompt 约定的 5 段【】结构
MOCK_AI_SUMMARY_OUTPUT = (
    "【背景】这是 AI 生成的背景段落，用于测试。\n\n"
    "【核心事实】事实 1：测试。事实 2：测试。\n\n"
    "【影响】影响 1：测试。\n\n"
    "【观点】观点 1：测试。\n\n"
    "【延伸】延伸话题 1：测试。"
)


@pytest.fixture
def mock_ai_summary(monkeypatch):
    """Mock ai_manager 用于 /trending/summary 端点测试。

    - is_available() -> True
    - generate() -> 固定 5 段【】结构字符串

    让 summary 测试不再依赖真实 AI（在 CI / 无 API key 环境也稳定）。
    """
    from backend.api import trending as _trending_mod

    async def fake_generate(prompt, **kwargs):
        return MOCK_AI_SUMMARY_OUTPUT

    monkeypatch.setattr(_trending_mod.ai_manager, "generate", fake_generate)
    monkeypatch.setattr(_trending_mod.ai_manager, "is_available", lambda: True)
    return MOCK_AI_SUMMARY_OUTPUT


@pytest.fixture
def mock_ai_summary_unavailable(monkeypatch):
    """Mock ai_manager.is_available() -> False，测 AI 不可用 → 503 路径。"""
    from backend.api import trending as _trending_mod

    async def fake_generate(prompt, **kwargs):
        return ""  # 不可达

    monkeypatch.setattr(_trending_mod.ai_manager, "generate", fake_generate)
    monkeypatch.setattr(_trending_mod.ai_manager, "is_available", lambda: False)
    return None


@pytest.fixture
def mock_ai_summary_empty_response(monkeypatch):
    """Mock ai_manager.generate() -> ""，测 AI 返回空 → 503 路径。"""
    from backend.api import trending as _trending_mod

    async def fake_generate(prompt, **kwargs):
        return ""

    monkeypatch.setattr(_trending_mod.ai_manager, "generate", fake_generate)
    monkeypatch.setattr(_trending_mod.ai_manager, "is_available", lambda: True)
    return None


# ========== C1 mock fixtures for copywriting / shoot_script e2e ==========

MOCK_AI_COPYWRITING_OUTPUT = {
    "id": "cpy_test_001",
    "title": "测试口播文案标题",
    "hooks": ["钩子 1", "钩子 2", "钩子 3"],
    "content": "这是测试用的口播文案内容。",
    "mode": "from_zero",
    "created_at": "2026-07-09T00:00:00",
}


@pytest.fixture
def mock_ai_copywriting(monkeypatch):
    """Mock copywriting_service.generate — 让 e2e 不依赖真实 AI。

    注意：patch 路径是 backend.api.copywriting.copywriting_service（API 模块 import 的实例），
    不是 backend.services.copywriting_service.copywriting_service（service 模块的实例）。
    """
    from backend.api import copywriting as _cpy_api
    from backend.models.domain.persona import CopywritingResponse

    async def fake_cpy_generate(request, db, user_id):
        return CopywritingResponse(
            id="cpy_test_001",
            title="测试口播文案",
            hooks=["钩子 1", "钩子 2"],
            content="这是测试文案内容。",
            mode=request.mode,
            persona=request.persona,  # 修复：CopywritingResponse 需要 persona 字段
            created_at="2026-07-09T00:00:00",
        )

    monkeypatch.setattr(_cpy_api.copywriting_service, "generate", fake_cpy_generate)
    return MOCK_AI_COPYWRITING_OUTPUT


@pytest.fixture
def mock_ai_shoot_script(monkeypatch):
    """Mock shoot_script_service.generate — 让 e2e 不依赖真实 AI。

    修复：patch 路径是 backend.api.shoot_script.shoot_script_service（API 模块 import 的实例），
    estimated_duration 是 string 不是 int。
    """
    from backend.api import shoot_script as _shoot_api
    from backend.models.domain.shoot_script import (
        ShootScriptResponse, PlatformType, ScriptStyle, Shot,
    )

    async def fake_shoot_generate(request):
        return ShootScriptResponse(
            id="shoot_test_001",
            title="测试脚本标题",
            topic=request.topic,
            platform=PlatformType.DOUYIN,
            style=request.style,
            persona=request.persona or "测试人设",  # ShootScriptResponse 需要 persona
            estimated_duration="0:00-1:00",  # 修复：必须是 string
            hooks=["钩子 1", "钩子 2"],
            shots=[
                Shot(
                    shot_number=1,
                    duration="0:00-0:08",
                    visual_description="画面描述",
                    dialogue="台词",
                    scene_suggestion="场景",
                    camera_movement="运镜",
                )
            ],
            call_to_action="行动号召",
            tags=["#测试"],
            created_at="2026-07-09T00:00:00",
        )

    monkeypatch.setattr(_shoot_api.shoot_script_service, "generate", fake_shoot_generate)
    return None
