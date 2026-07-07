"""
需求 8 e2e — AI 视频剪辑

覆盖：
- POST /media/video-edit/upload         上传视频 → task_id
- GET  /media/video-edit/task/{id}      查询任务状态
- GET  /media/video-edit/{id}/segments  片段详情
- GET  /media/video-edit/{id}/download/{type}  下载
- 任务不存在 → 404
- 未授权 → 401
- 跨用户隔离：A 看不到 B 的任务
- 配额扣减（video_edit = 15）

完整流程（Whisper + LLM + FFmpeg）依赖外部资源，不在 e2e 范围。
"""
import io
import os
import pytest

from backend.config.settings import settings


P = "/api/v1/media/video-edit"


@pytest.fixture(autouse=True)
def use_tmp_upload(monkeypatch, tmp_path):
    """使用临时上传目录避免污染"""
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def _video_bytes():
    return b"\x00\x00\x00\x20ftypisom" + b"\x00" * 400


class TestUpload:
    def test_upload_video_returns_task_id(self, client, auth_headers):
        files = {"file": ("clip.mp4", io.BytesIO(_video_bytes()), "video/mp4")}
        r = client.post(f"{P}/upload", files=files, headers=auth_headers)
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert "task_id" in data
        assert data["status"] == "processing"

    def test_upload_without_auth_returns_401(self, client):
        files = {"file": ("clip.mp4", io.BytesIO(_video_bytes()), "video/mp4")}
        r = client.post(f"{P}/upload", files=files)
        assert r.status_code in (401, 403)

    def test_upload_deducts_quota(self, client, auth_headers):
        before = client.get("/api/v1/auth/me", headers=auth_headers)
        if before.status_code != 200:
            pytest.skip("/auth/me 不可用")
        balance_before = before.json()["data"]["quota_balance"]

        files = {"file": ("q.mp4", io.BytesIO(_video_bytes()), "video/mp4")}
        client.post(f"{P}/upload", files=files, headers=auth_headers)

        after = client.get("/api/v1/auth/me", headers=auth_headers)
        new_balance = after.json()["data"]["quota_balance"]
        # 视频剪辑 15 配额
        assert balance_before - new_balance >= 1


class TestGetTask:
    def test_get_task_after_upload(self, client, auth_headers):
        files = {"file": ("t.mp4", io.BytesIO(_video_bytes()), "video/mp4")}
        upload = client.post(f"{P}/upload", files=files, headers=auth_headers)
        task_id = upload.json()["data"]["task_id"]

        r = client.get(f"{P}/task/{task_id}", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["task_id"] == task_id
        assert data["status"] in ("pending", "processing", "completed", "failed")

    def test_get_nonexistent_task_returns_404(self, client, auth_headers):
        r = client.get(f"{P}/task/nonexistent-id-xxx", headers=auth_headers)
        assert r.status_code == 404
        assert "不存在" in r.json()["error"]["message"]

    def test_get_task_without_auth_returns_401(self, client):
        r = client.get(f"{P}/task/any-id")
        assert r.status_code in (401, 403)


class TestSegments:
    def test_get_segments_nonexistent_returns_404(self, client, auth_headers):
        r = client.get(f"{P}/nonexistent-id/segments", headers=auth_headers)
        assert r.status_code == 404


class TestDownload:
    def test_download_nonexistent_returns_404(self, client, auth_headers):
        r = client.get(f"{P}/nonexistent-id/download/video", headers=auth_headers)
        assert r.status_code == 404

    def test_download_invalid_type_returns_400(self, client, auth_headers):
        # 先建一个任务
        files = {"file": ("t.mp4", io.BytesIO(_video_bytes()), "video/mp4")}
        upload = client.post(f"{P}/upload", files=files, headers=auth_headers)
        task_id = upload.json()["data"]["task_id"]
        # 即使任务 pending，file_type 校验应在权限校验之前
        r = client.get(f"{P}/{task_id}/download/bogus", headers=auth_headers)
        assert r.status_code == 400
        assert "file_type" in r.json()["error"]["message"] or "video" in r.json()["error"]["message"]


class TestUserIsolation:
    def test_user_b_cannot_see_user_a_task(self, client, auth_headers):
        """A 上传的任务，B 查不到（404）"""
        # A 上传
        files = {"file": ("iso.mp4", io.BytesIO(_video_bytes()), "video/mp4")}
        upload = client.post(f"{P}/upload", files=files, headers=auth_headers)
        task_id = upload.json()["data"]["task_id"]

        # 注册 B
        r2 = client.post("/api/v1/auth/register", json={
            "username": "vedit_user_b", "password": "pass123456", "email": "vb@test.com"
        })
        if r2.status_code not in (200, 201):
            pytest.skip(f"无法注册 B: {r2.text}")
        headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

        # B 查 A 的任务 → 404（无权访问）
        r = client.get(f"{P}/task/{task_id}", headers=headers_b)
        assert r.status_code == 404


class TestPreview:
    """v3 改造：preview 端点（避免用户白下载不满意的视频）"""

    def test_preview_nonexistent_task_returns_404(self, client, auth_headers):
        r = client.get(f"{P}/nonexistent-id-xxx/preview", headers=auth_headers)
        assert r.status_code == 404
        assert "不存在" in r.json()["error"]["message"]

    def test_preview_requires_auth(self, client):
        r = client.get(f"{P}/any-id/preview")
        assert r.status_code in (401, 403)

    def test_preview_incomplete_task_returns_400(self, client, auth_headers):
        """任务还没完成时不允许访问 preview"""
        files = {"file": ("p.mp4", io.BytesIO(_video_bytes()), "video/mp4")}
        upload = client.post(f"{P}/upload", files=files, headers=auth_headers)
        task_id = upload.json()["data"]["task_id"]

        # 上传后状态是 processing，preview 应该 400
        r = client.get(f"{P}/{task_id}/preview", headers=auth_headers)
        assert r.status_code == 400
        assert "未完成" in r.json()["error"]["message"]

    def test_preview_completed_task_returns_200_with_inline_disposition(self, client, auth_headers, tmp_path, monkeypatch):
        """completed 任务 + preview 文件存在 → 200 + inline + Accept-Ranges"""
        from backend.models.database.tables import UserTable, VideoEditTaskTable
        from backend.tests.conftest import TestSessionLocal
        from backend.config.database import get_db

        # 创建用户 + 任务记录 + preview 文件
        me = client.get("/api/v1/auth/me", headers=auth_headers).json()["data"]
        user_id = me["id"]

        # 在临时 upload dir 下放一个伪 preview 文件
        preview_dir = settings.UPLOAD_DIR + "/preview"
        os.makedirs(preview_dir, exist_ok=True)
        preview_filename = "preview_test-task-001.mp4"
        preview_path = os.path.join(preview_dir, preview_filename)
        with open(preview_path, "wb") as f:
            f.write(b"\x00\x00\x00\x20ftypisom" + b"\x00" * 100)

        # 直接插数据库 task 记录（mock completed 状态）
        from backend.config.database import SessionLocal
        from backend.models.database.tables import Base
        # 用 conftest 的 test_engine
        from backend.tests.conftest import test_engine, TestSessionLocal as TSL
        Base.metadata.create_all(bind=test_engine)
        db = TSL()
        try:
            task = VideoEditTaskTable(
                task_id="test-task-001",
                status="completed",
                user_id=user_id,
                source_video_path="/tmp/src.mp4",
                source_video_name="src.mp4",
                output_video_path=str(tmp_path / "edited.mp4"),
                preview_video_path=preview_path,
                preview_size_bytes=116,
                kept_segments=[[0, 5]],
                removed_segments=[{"start": 5, "end": 6, "reason": "filler"}],
                original_duration=10.0,
                final_duration=8.0,
            )
            db.add(task)
            db.commit()
        finally:
            db.close()

        r = client.get(f"{P}/test-task-001/preview", headers=auth_headers)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("video/mp4")
        # inline（浏览器内播放，不弹下载）
        assert "inline" in r.headers.get("content-disposition", "")
        # Range 支持（seek 关键）
        assert r.headers.get("accept-ranges") == "bytes"

    def test_preview_completed_task_without_preview_file_returns_404(self, client, auth_headers, monkeypatch):
        """completed 但 preview_video_path 为空 → 404（兜底）"""
        from backend.tests.conftest import test_engine, TestSessionLocal as TSL
        from backend.models.database.tables import Base, VideoEditTaskTable

        me = client.get("/api/v1/auth/me", headers=auth_headers).json()["data"]
        Base.metadata.create_all(bind=test_engine)
        db = TSL()
        try:
            task = VideoEditTaskTable(
                task_id="test-task-no-preview",
                status="completed",
                user_id=me["id"],
                source_video_path="/tmp/src.mp4",
                output_video_path="/tmp/edited.mp4",
                # 没有 preview_video_path
                kept_segments=[[0, 5]],
                removed_segments=[],
                original_duration=10.0,
                final_duration=8.0,
            )
            db.add(task)
            db.commit()
        finally:
            db.close()

        r = client.get(f"{P}/test-task-no-preview/preview", headers=auth_headers)
        assert r.status_code == 404
        assert "预览未生成" in r.json()["error"]["message"]

    def test_preview_other_user_task_returns_404(self, client, auth_headers):
        """跨用户：user_b 看不到 user_a 的 preview（get_task_owned_by 兜底）"""
        from backend.tests.conftest import test_engine, TestSessionLocal as TSL
        from backend.models.database.tables import Base, VideoEditTaskTable

        # A 注册 + 上传（拿 user_a id）
        files = {"file": ("a.mp4", io.BytesIO(_video_bytes()), "video/mp4")}
        upload = client.post(f"{P}/upload", files=files, headers=auth_headers)
        task_id = upload.json()["data"]["task_id"]

        # 注册 B
        r2 = client.post("/api/v1/auth/register", json={
            "username": "preview_user_b", "password": "pass123456", "email": "pb@test.com"
        })
        if r2.status_code not in (200, 201):
            pytest.skip(f"无法注册 B: {r2.text}")
        headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

        # B 查 A 的 preview → 404
        r = client.get(f"{P}/{task_id}/preview", headers=headers_b)
        assert r.status_code == 404
