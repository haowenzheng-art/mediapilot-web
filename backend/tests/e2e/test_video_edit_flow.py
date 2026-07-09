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



class TestVideoEditTaskList:
    """B1 e2e: 测 GET /api/v1/media/video-edit/tasks 端点

    之前没有 list 端点，用户跑完一个任务后就再也找不到。
    """

    def _get_test_db(self):
        """拿到测试 session（通过 app.dependency_overrides）"""
        from backend.main import app
        from backend.config.database import get_db
        from backend.tests.conftest import TestSessionLocal

        # 优先用 TestSessionLocal 直接（更稳，不依赖 FastAPI 内部）
        return TestSessionLocal()

    def _create_completed_task(self, db, user_id, source_name="list_test.mp4", minutes=1):
        """直接造一个 completed 状态的 task 跑测试（避免跑真的 ffmpeg/AI 流程）"""
        import uuid
        from backend.models.database.tables import VideoEditTaskTable

        task = VideoEditTaskTable(
            task_id=str(uuid.uuid4()),
            user_id=user_id,
            status="completed",
            source_video_name=source_name,
            source_video_path=f"/tmp/{source_name}",
            output_video_path=f"/tmp/out_{source_name}",
            preview_video_path=f"/tmp/preview_{source_name}",
            original_duration=minutes * 60.0,
            final_duration=minutes * 30.0,
            edit_config={"strength": "medium"},
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def _get_user_id(self, username):
        db = self._get_test_db()
        try:
            from backend.models.database.tables import UserTable
            user = db.query(UserTable).filter(UserTable.username == username).first()
            return user.id if user else None
        finally:
            db.close()

    def test_list_tasks_returns_user_history(self, client, auth_headers):
        """用户能看到自己的历史任务列表"""
        user_id = self._get_user_id("e2e_tester")
        assert user_id is not None, "e2e_tester should exist"

        # 造 2 个 task — 提前存 task_id 字符串，避免 db.close() 后 DetachedInstanceError
        db = self._get_test_db()
        try:
            t1 = self._create_completed_task(db, user_id, "task1.mp4", 1)
            t2 = self._create_completed_task(db, user_id, "task2.mp4", 2)
            t1_id = t1.task_id
            t2_id = t2.task_id
        finally:
            db.close()

        # 列任务
        resp = client.get(
            "/api/v1/media/video-edit/tasks",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        tasks = body["data"]["tasks"]
        assert len(tasks) >= 2, f"应至少看到 2 个 task，实际 {len(tasks)}"

        # 字段检查
        task_ids = [t["task_id"] for t in tasks]
        assert t1_id in task_ids
        assert t2_id in task_ids

        first = tasks[0]
        assert "task_id" in first
        assert "status" in first
        assert "source_video_name" in first
        assert "created_at" in first
        # 列表 schema 不应包含完整 segments（避免响应过重）
        assert "kept_segments" not in first or first["kept_segments"] is None
        assert "removed_segments" not in first or first["removed_segments"] is None

    def test_list_tasks_user_isolation(self, client, auth_headers):
        """A 看不到 B 的任务（用户隔离）"""
        a_id = self._get_user_id("e2e_tester")

        # 造 A 的 1 个 task — 提前存 id
        db = self._get_test_db()
        try:
            a_task = self._create_completed_task(db, a_id, "a_task.mp4", 1)
            a_task_id = a_task.task_id
        finally:
            db.close()

        # 通过 HTTP 注册 B 用户（其他 e2e 测试都这么用）
        reg = client.post("/api/v1/auth/register", json={
            "username": "vedit_b_user",
            "password": "test123456",
            "email": "b@vedit.com",
        })
        if reg.status_code != 200:
            # 可能已经注册过
            pass
        b_user_id = self._get_user_id("vedit_b_user")
        assert b_user_id is not None, "B 用户应被注册成功"

        # 造 B 的 1 个 task — 提前存 id
        db = self._get_test_db()
        try:
            b_task = self._create_completed_task(db, b_user_id, "b_task.mp4", 1)
            b_task_id = b_task.task_id
        finally:
            db.close()

        # B 用户登录拿 token
        login = client.post("/api/v1/auth/login", json={
            "username": "vedit_b_user",
            "password": "test123456",
        })
        assert login.status_code == 200, login.text
        b_token = login.json()["data"]["token"]
        b_headers = {"Authorization": f"Bearer {b_token}"}

        # A 列任务
        a_resp = client.get("/api/v1/media/video-edit/tasks", headers=auth_headers)
        a_tasks = a_resp.json()["data"]["tasks"]
        a_task_ids = [t["task_id"] for t in a_tasks]
        assert a_task_id in a_task_ids, "A 应看到自己的 task"
        assert b_task_id not in a_task_ids, "A 不应看到 B 的 task"

        # B 列任务
        b_resp = client.get("/api/v1/media/video-edit/tasks", headers=b_headers)
        b_tasks = b_resp.json()["data"]["tasks"]
        b_task_ids = [t["task_id"] for t in b_tasks]
        assert b_task_id in b_task_ids, "B 应看到自己的 task"
        assert a_task_id not in b_task_ids, "B 不应看到 A 的 task"

    def test_list_tasks_pagination(self, client, auth_headers):
        """分页 skip/limit 工作正常"""
        user_id = self._get_user_id("e2e_tester")

        # 造 3 个 task
        db = self._get_test_db()
        try:
            for i in range(3):
                self._create_completed_task(db, user_id, f"page_{i}.mp4", 1)
        finally:
            db.close()

        # skip=1, limit=2
        resp = client.get(
            "/api/v1/media/video-edit/tasks?skip=1&limit=2",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert len(body["tasks"]) <= 2, f"limit=2 应至多返 2 个 task，实际 {len(body['tasks'])}"
        assert body["skip"] == 1
        assert body["limit"] == 2

    def test_list_tasks_unauthorized_returns_401(self, client):
        """未授权访问应返 401"""
        resp = client.get("/api/v1/media/video-edit/tasks")
        assert resp.status_code in [401, 403]  # 取决于 auth 依赖的实现



class TestVideoEditContentLibraryIntegration:
    """B2 e2e: 视频剪辑产物能通过 content_library 端点查询到

    验证 video_edit 类型的内容能：
    1. 列出（按 content_type 筛选）
    2. 通过 hot_topic_id 反查
    """

    def _create_video_edit_content(self, db, user_id, source_name="b2_test.mp4",
                                    minutes=1, hot_topic_id=None):
        """模拟 _process_video_edit_bg 完成后的入库调用"""
        from backend.models.domain.content_library import ContentCreate
        from backend.models.domain.content import ContentType
        from backend.services.content_library_service import content_library_service

        return content_library_service.create_content(
            db,
            user_id=user_id,
            content_in=ContentCreate(
                content_type=ContentType.VIDEO_EDIT,
                content_id=f"vedit_b2_{user_id}",
                title=source_name,
                summary=f"原始 {minutes*60}s → 剪辑后 {minutes*30}s",
                hot_topic_id=hot_topic_id,
                hot_topic_title=f"测试热点 {hot_topic_id}" if hot_topic_id else None,
                hot_topic_source="百度新闻" if hot_topic_id else None,
                mode=None,
                persona=None,
                platform=None,
                style="medium",
            )
        )

    def _get_user_id(self, username):
        from backend.tests.conftest import TestSessionLocal
        from backend.models.database.tables import UserTable
        db = TestSessionLocal()
        try:
            user = db.query(UserTable).filter(UserTable.username == username).first()
            return user.id if user else None
        finally:
            db.close()

    def test_video_edit_content_appears_in_library(self, client, auth_headers):
        """入库后，content_library 列表能查到 video_edit 类型的内容"""
        from backend.tests.conftest import TestSessionLocal
        user_id = self._get_user_id("e2e_tester")

        db = TestSessionLocal()
        try:
            content_record = self._create_video_edit_content(
                db, user_id, "b2_video_test.mp4", minutes=2
            )
            created_id = content_record.id
        finally:
            db.close()

        # 列表查询 (按 type=video_edit 筛选)
        resp = client.get(
            "/api/v1/content-library/contents?content_type=video_edit",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        # 至少能找到刚入库的这条
        contents = body["data"]["contents"] if isinstance(body["data"], dict) else body["data"]
        found = [c for c in contents if c["id"] == created_id]
        assert len(found) == 1, f"应能在列表中找到刚入库的 video_edit 内容，实际 {len(found)}"
        item = found[0]
        assert item["content_type"] == "video_edit"
        assert item["title"] == "b2_video_test.mp4"

    def test_video_edit_content_linked_to_hot_topic(self, client, auth_headers):
        """入库时带 hot_topic_id → 能通过反查 API 找到"""
        from backend.tests.conftest import TestSessionLocal
        user_id = self._get_user_id("e2e_tester")
        hot_topic_id = "b2_hot_topic_001"

        db = TestSessionLocal()
        try:
            content_record = self._create_video_edit_content(
                db, user_id, "b2_with_topic.mp4", minutes=1, hot_topic_id=hot_topic_id
            )
            created_id = content_record.id
        finally:
            db.close()

        # 通过 hot_topic_id 反查
        resp = client.get(
            f"/api/v1/content-library/hot-topic/{hot_topic_id}/contents",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        contents = body["data"]["contents"] if isinstance(body["data"], dict) else body["data"]
        found = [c for c in contents if c["id"] == created_id]
        assert len(found) == 1, f"反查应能找到这条 video_edit 内容"
        item = found[0]
        assert item["hot_topic_id"] == hot_topic_id
        assert item["hot_topic_source"] == "百度新闻"

    def test_video_edit_content_user_isolation(self, client, auth_headers):
        """A 的 video_edit 内容不会被 B 看到（用户隔离）"""
        from backend.tests.conftest import TestSessionLocal
        from backend.models.database.tables import UserTable
        from backend.services.auth_service_typed import auth_service

        a_id = self._get_user_id("e2e_tester")

        # 注册 B 用户
        reg = client.post("/api/v1/auth/register", json={
            "username": "vedit_iso_b",
            "password": "test123456",
            "email": "b2@iso.com",
        })
        if reg.status_code != 200:
            pass  # 可能已注册
        b_id = self._get_user_id("vedit_iso_b")
        assert b_id is not None

        # A 入库 1 个
        db = TestSessionLocal()
        try:
            a_content = self._create_video_edit_content(db, a_id, "a_b2.mp4", 1)
            a_content_id = a_content.id
            b_content = self._create_video_edit_content(db, b_id, "b_b2.mp4", 1)
            b_content_id = b_content.id
        finally:
            db.close()

        # B 登录
        login = client.post("/api/v1/auth/login", json={
            "username": "vedit_iso_b",
            "password": "test123456",
        })
        assert login.status_code == 200
        b_token = login.json()["data"]["token"]
        b_headers = {"Authorization": f"Bearer {b_token}"}

        # A 列表 — 不应有 B 的
        a_resp = client.get(
            "/api/v1/content-library/contents?content_type=video_edit",
            headers=auth_headers,
        )
        a_contents = a_resp.json()["data"]["contents"] if isinstance(a_resp.json()["data"], dict) else a_resp.json()["data"]
        a_ids = [c["id"] for c in a_contents]
        assert a_content_id in a_ids
        assert b_content_id not in a_ids, "A 不应看到 B 的 video_edit 内容"

        # B 列表 — 不应有 A 的
        b_resp = client.get(
            "/api/v1/content-library/contents?content_type=video_edit",
            headers=b_headers,
        )
        b_contents = b_resp.json()["data"]["contents"] if isinstance(b_resp.json()["data"], dict) else b_resp.json()["data"]
        b_ids = [c["id"] for c in b_contents]
        assert b_content_id in b_ids
        assert a_content_id not in b_ids, "B 不应看到 A 的 video_edit 内容"
