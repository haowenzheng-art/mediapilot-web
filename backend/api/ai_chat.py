"""
AI Chat 路由 - 前端直接调用 AI AI 功能
"""
import json
import sys
import os
from typing import Optional, List
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.core.ai_service import ai_manager
from backend.services.product_tutor_service import product_tutor_service

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

        # 使用异步的 generate 方法
        result = await ai_manager.generate(prompt, max_tokens=request.max_tokens)

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
            # AIChat 场景不需要深度思考，传 enable_reasoning=False
            async for event in ai_manager.generate_stream(
                prompt, max_tokens=request.max_tokens, enable_reasoning=False
            ):
                # ai_manager 现在 yield 事件对象 {"type": "content"|"reasoning", "delta": "..."}
                # 透传给前端时仅取 content 字段，保持现有 OpenAI 兼容协议
                if event.get("type") == "content":
                    yield "data: " + json.dumps({
                        "choices": [{"delta": {"content": event["delta"]}}]
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


# ============ 产品教程 (Product Tutor) ============

class TutorRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="用户问题")


@router.post("/tutor")
async def tutor_endpoint(request: TutorRequest):
    """
    产品教程接口
    - 关键词命中产品知识库 → 直接返回 FAQ + 跳转动作
    - 未命中且 LLM 可用 → 用 KB 做检索增强兜底
    - 未命中且 LLM 不可用 → 返回引导话术
    """
    reply = await product_tutor_service.ask(request.query)
    return {
        "matched": reply.matched,
        "source": reply.source,
        "faq_id": reply.faq_id,
        "answer": reply.answer,
        "action_url": reply.action_url,
        "action_text": reply.action_text,
    }


@router.get("/tutor/faqs")
async def list_faqs():
    """列出产品教程支持的所有 FAQ（前端可作为快速提问按钮）"""
    return {
        "total": len(product_tutor_service.faqs),
        "faqs": [
            {
                "id": f.id,
                "question": f.question,
                "action_url": f.action_url,
                "action_text": f.action_text,
            }
            for f in product_tutor_service.faqs
        ],
    }
