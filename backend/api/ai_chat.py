"""
AI Chat 路由 - 前端直接调用 AI AI 功能
"""
import json
import sys
import os
from typing import Optional, List
from pydantic import BaseModel, Field

# 设置项目根目录（MediaPilot/）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.core.ai_service import ai_manager

router = APIRouter(prefix="/ai", tags=["AI Chat"])

# 确保在模块加载时尝试配置 AI 服务
try:
    from backend.config.settings import settings
    if not ai_manager.current_provider and settings.AI_API_KEY:
        ai_manager.configure(
            provider=settings.AI_PROVIDER,
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_BASE_URL,
            model=settings.AI_MODEL,
            timeout=settings.AI_TIMEOUT,
            max_retries=settings.AI_MAX_RETRIES
        )
except:
    pass


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: int = 1500
    temperature: float = 0.6


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """AI 聊天接口（非流式）"""
    if not ai_manager.is_available():
        raise HTTPException(status_code=503, detail="AI服务未配置或不可用")

    try:
        prompt = request.messages[0].content if request.messages else ""

        # 使用同步的 generate 方法
        result = ai_manager.generate(prompt, max_tokens=request.max_tokens)

        return {"content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """AI 聊天接口（流式输出）"""
    if not ai_manager.is_available():
        async def error_stream():
            yield "data: " + json.dumps({"error": "AI服务未配置或不可用"}) + "\n\n"
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"}
        )

    if not request.messages:
        async def error_stream():
            yield "data: " + json.dumps({"error": "缺少messages参数"}) + "\n\n"
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"}
        )

    # 获取用户消息内容
    prompt = ""
    for msg in request.messages:
        if msg.role == "user":
            prompt = msg.content
            break

    async def stream_generator():
        try:
            async for chunk in ai_manager.generate_stream(prompt, max_tokens=request.max_tokens):
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
