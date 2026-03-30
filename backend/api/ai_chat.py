"""
AI Chat 路由 - 前端直接调用 AI AI 功能
"""
import json
import sys
import os

# 设置项目根目录（MediaPilot/）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.core.ai_service import ai_manager

router = APIRouter(prefix="/ai", tags=["AI Chat"])


@router.post("/chat")
async def chat_endpoint(request: dict):
    """AI 聊天接口（非流式）"""
    if not ai_manager.is_available():
        raise HTTPException(status_code=503, detail="AI服务未配置或不可用")

    try:
        messages = request.get("messages", [])
        max_tokens = request.get("max_tokens", 1500)
        temperature = request.get("temperature", 0.6)

        result = await ai_manager.generate_stream(messages[0].get("content", ""), max_tokens=max_tokens)
        full_text = ""
        async for chunk in result:
            full_text += chunk

        return {"content": full_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream_endpoint(request: dict):
    """AI 聊天接口（流式输出）"""
    if not ai_manager.is_available():
        async def error_stream():
            yield "data: " + json.dumps({"error": "AI服务未配置或不可用"}) + "\n\n"
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"}
        )

    messages = request.get("messages", [])
    max_tokens = request.get("max_tokens", 1500)
    temperature = request.get("temperature", 0.6)

    if not messages:
        async def error_stream():
            yield "data: " + json.dumps({"error": "缺少messages参数"}) + "\n\n"
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"}
        )

    # 获取用户消息内容
    prompt = ""
    for msg in messages:
        if msg.get("role") == "user":
            prompt = msg.get("content", "")
            break

    async def stream_generator():
        try:
            async for chunk in ai_manager.generate_stream(prompt, max_tokens=max_tokens):
                yield "data: " + json.dumps({
                    "choices": [{"delta": {"content": chunk}}]
                }) + "\n\n"

            # 发送完成标记
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield "data: " + json.dumps({"error": str(e)}) + "\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )
