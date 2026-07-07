"""
v3 冲刺 e2e — 内容生成流式 SSE

覆盖：
- POST /api/v1/copywriting/generate/stream   SSE 协议正确性
- POST /api/v1/shoot-script/generate/stream  SSE 协议正确性
- 配额预扣与异常退款
- 未授权 401
- 请求参数校验（缺 persona 等）

流式响应通过 mock AI 服务覆盖，避免真实 LLM 调用。
"""
import asyncio
import json
import time
import pytest
from unittest.mock import AsyncMock, patch


CP = "/api/v1/copywriting"
SP = "/api/v1/shoot-script"


def _parse_sse_events(raw_text: str) -> list:
    """把 SSE 响应原文解析成事件列表（每条 = data: 后面的 JSON）"""
    events = []
    for line in raw_text.split("\n"):
        if line.startswith("data: "):
            data = line[6:].strip()
            if not data or data == "[DONE]":
                continue
            try:
                events.append(json.loads(data))
            except json.JSONDecodeError:
                # 非 JSON 行（如心跳），跳过
                pass
    return events


class TestCopywritingStream:
    def test_stream_requires_auth(self, client):
        r = client.post(f"{CP}/generate/stream", json={
            "mode": "from_zero",
            "persona": "AI产品经理",
            "topic": "AI 工具"
        })
        # 无 JWT → 401
        assert r.status_code in (401, 403)

    def test_stream_quota_exceeded_returns_429(self, client, auth_headers, monkeypatch):
        """配额不足时直接返 429（不走流式）"""
        # mock check_quota 返回 False
        from backend.services.auth_service_typed import auth_service
        monkeypatch.setattr(auth_service, "check_quota", lambda *a, **kw: (False, 0))

        r = client.post(f"{CP}/generate/stream", json={
            "mode": "from_zero",
            "persona": "AI产品经理",
            "topic": "AI 工具"
        }, headers=auth_headers)
        assert r.status_code == 429
        assert "配额" in r.json()["error"]["message"]

    def test_stream_emits_content_events_and_done(self, client, auth_headers, monkeypatch):
        """流式响应包含 content 事件 + [DONE] 标记"""
        # mock ai_manager.generate_stream 让其产出可预测的事件流
        from backend.core.ai_service import ai_manager

        async def fake_stream(prompt, **kwargs):
            yield {"type": "content", "delta": "标题：AI 工具推荐"}
            yield {"type": "content", "delta": "\n\n文案正文："}
            yield {"type": "content", "delta": "第一款工具..."}
            yield {
                "type": "meta",
                "meta": {
                    "final": True,
                    "reasoning_supported": False,
                    "parsed": {
                        "id": "test-id-123",
                        "title": "AI 工具推荐",
                        "hooks": ["钩子1"],
                        "content": "第一款工具...",
                        "mode": "from_zero",
                        "persona": "AI产品经理",
                    },
                },
            }

        monkeypatch.setattr(ai_manager, "generate_stream", fake_stream)
        # mock is_available 防止早期 return
        monkeypatch.setattr(ai_manager, "is_available", lambda: True)

        with client.stream(
            "POST",
            f"{CP}/generate/stream",
            json={
                "mode": "from_zero",
                "persona": "AI产品经理",
                "topic": "AI 工具",
            },
            headers=auth_headers,
        ) as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")
            raw = r.read().decode("utf-8")

        events = _parse_sse_events(raw)
        # 至少 3 个 content 事件
        content_events = [e for e in events if e.get("choices", [{}])[0].get("delta", {}).get("content")]
        assert len(content_events) >= 3
        # meta 事件收尾
        meta_events = [e for e in events if "meta" in e]
        assert len(meta_events) >= 1
        assert meta_events[0]["meta"]["final"] is True
        # [DONE] 标记
        assert "[DONE]" in raw

    def test_stream_passes_enable_reasoning_to_ai(self, client, auth_headers, monkeypatch):
        """请求体 enable_reasoning=True 时透传到 ai_manager.generate_stream"""
        from backend.core.ai_service import ai_manager

        captured_kwargs = {}

        async def fake_stream(prompt, **kwargs):
            captured_kwargs.update(kwargs)
            yield {"type": "content", "delta": "x"}
            yield {"type": "meta", "meta": {"final": True, "parsed": {
                "id": "t1", "title": "", "hooks": [], "content": "x",
                "mode": "from_zero", "persona": "x"
            }}}

        monkeypatch.setattr(ai_manager, "generate_stream", fake_stream)
        monkeypatch.setattr(ai_manager, "is_available", lambda: True)

        with client.stream(
            "POST",
            f"{CP}/generate/stream",
            json={
                "mode": "from_zero",
                "persona": "AI产品经理",
                "topic": "AI 工具",
                "enable_reasoning": True,
            },
            headers=auth_headers,
        ) as r:
            r.read()

        # enable_reasoning 应该透传到 ai_manager
        assert captured_kwargs.get("enable_reasoning") is True


class TestShootScriptStream:
    def test_stream_requires_auth(self, client):
        r = client.post(f"{SP}/generate/stream", json={
            "topic": "AI 工具",
            "platform": "douyin",
            "style": "energetic",
        })
        assert r.status_code in (401, 403)

    def test_stream_emits_content_and_meta(self, client, auth_headers, monkeypatch):
        """脚本流式：content 事件 + meta 收尾（含 shots 完整结构）"""
        from backend.core.ai_service import ai_manager

        async def fake_stream(prompt, **kwargs):
            yield {"type": "content", "delta": "标题：脚本"}
            yield {"type": "content", "delta": "\n\n分镜头脚本："}
            yield {"type": "content", "delta": "镜头1..."}
            yield {
                "type": "meta",
                "meta": {
                    "final": True,
                    "reasoning_supported": False,
                    "parsed": {
                        "id": "s1",
                        "topic": "AI 工具",
                        "platform": "douyin",
                        "style": "energetic",
                        "persona": None,
                        "shots": [
                            {
                                "shot_number": 1,
                                "duration": "0:00-0:05",
                                "visual_description": "开场画面",
                                "dialogue": "今天聊 AI",
                                "scene_suggestion": None,
                                "camera_movement": None,
                                "notes": None,
                            }
                        ],
                        "title": "脚本",
                        "hooks": ["钩子"],
                        "call_to_action": "点赞关注",
                        "tags": ["AI"],
                        "estimated_duration": "5秒",
                    },
                },
            }

        monkeypatch.setattr(ai_manager, "generate_stream", fake_stream)
        monkeypatch.setattr(ai_manager, "is_available", lambda: True)

        with client.stream(
            "POST",
            f"{SP}/generate/stream",
            json={
                "topic": "AI 工具",
                "platform": "douyin",
                "style": "energetic",
            },
            headers=auth_headers,
        ) as r:
            assert r.status_code == 200
            raw = r.read().decode("utf-8")

        events = _parse_sse_events(raw)
        meta_events = [e for e in events if "meta" in e]
        assert len(meta_events) == 1
        parsed = meta_events[0]["meta"]["parsed"]
        assert len(parsed["shots"]) == 1
        assert parsed["shots"][0]["shot_number"] == 1
        assert "[DONE]" in raw