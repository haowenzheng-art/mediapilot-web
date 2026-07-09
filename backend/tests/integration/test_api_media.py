"""
媒体处理 API 集成测试
"""
import pytest
import io
import os
from unittest.mock import patch

from backend.config.settings import settings
from backend.tests.conftest import TestSessionLocal


@pytest.fixture(autouse=True)
def force_mock_transcribe(monkeypatch, tmp_path):
    """D 任务清理后：MediaProcessor.transcribe_audio 不再隐式降级 mock，
    必须显式开 USE_MOCK_TRANSCRIBE 让 MediaService 走 MockMediaProcessor。
    否则后台转写会因 transcribe_engine 未配置而 raise → task 永远进 failed。
    """
    monkeypatch.setattr(settings, "USE_MOCK_TRANSCRIBE", True)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@pytest.fixture
def media_auth(client, registered_user, auth_headers):
    """返回认证后的 client + headers"""
    return client, auth_headers


class TestMediaUploadAPI:
    """媒体上传 API 测试"""

    def test_upload_audio_file(self, client, registered_user, auth_headers):
        """测试上传音频文件"""
        audio_content = b"fake audio data"
        file = io.BytesIO(audio_content)

        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data["data"]
        assert "status" in data["data"]

    def test_upload_video_file(self, client, registered_user, auth_headers):
        """测试上传视频文件"""
        video_content = b"fake video data"
        file = io.BytesIO(video_content)

        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.mp4", file, "video/mp4")},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_upload_requires_auth(self, client):
        """上传需要认证"""
        audio_content = b"fake audio data"
        file = io.BytesIO(audio_content)

        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 401

    def test_upload_deducts_quota(self, client, registered_user, auth_headers):
        """上传会扣减配额"""
        quota_before = registered_user["user"]["quota_balance"]

        audio_content = b"fake audio data"
        file = io.BytesIO(audio_content)

        client.post(
            "/api/v1/media/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")},
            headers=auth_headers
        )

        me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
        quota_after = me_resp.json()["data"]["quota_balance"]
        assert quota_after < quota_before


class TestMediaTaskAPI:
    """媒体任务查询 API 测试"""

    def test_get_task_status(self, client, registered_user, auth_headers):
        """测试获取任务状态"""
        import time

        audio_content = b"fake audio data"
        file = io.BytesIO(audio_content)

        upload_resp = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")},
            headers=auth_headers
        )
        task_id = upload_resp.json()["data"]["task_id"]

        # 后台任务异步处理，轮询推进事件循环直到离开 pending（最多 ~10s）
        data = None
        for _ in range(50):
            response = client.get(f"/api/v1/media/task/{task_id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            if data["data"]["status"] != "pending":
                break
            time.sleep(0.2)

        assert data["success"] is True
        assert data["data"]["status"] in ["processing", "completed", "failed"]

    def test_get_completed_task_result(self, client, registered_user, auth_headers):
        """测试获取已完成任务的结果"""
        import time

        audio_content = b"fake audio data"
        file = io.BytesIO(audio_content)

        upload_resp = client.post(
            "/api/v1/media/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")},
            headers=auth_headers
        )
        task_id = upload_resp.json()["data"]["task_id"]

        # 轮询推进后台处理直到进入终态（最多 ~10s）
        result = None
        for _ in range(50):
            response = client.get(f"/api/v1/media/task/{task_id}", headers=auth_headers)
            assert response.status_code == 200
            result = response.json()["data"]
            if result["status"] in ["completed", "failed"]:
                break
            time.sleep(0.2)

        assert result["status"] == "completed"
        assert "transcript" in result
        assert "outline" in result
        assert "timestamps" in result

    def test_get_nonexistent_task(self, client, registered_user, auth_headers):
        """测试获取不存在的任务"""
        response = client.get("/api/v1/media/task/nonexistent-id", headers=auth_headers)

        assert response.status_code == 404
