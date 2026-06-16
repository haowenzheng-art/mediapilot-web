"""
Agent 路由 — ReAct 智能体对话接口
"""
import json
import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from backend.config.database import get_db
from backend.models.database.tables import UserTable
from backend.api.dependencies import get_current_user
from backend.services.agent_executor import AgentExecutor
from backend.services.agent_service import tool_registry
from backend.utils.api_response import success_response, error_response, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent"])


class AgentRequest(BaseModel):
    """Agent 请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户指令")
    max_iterations: Optional[int] = Field(5, ge=1, le=10, description="最大思考步数")


class ToolListResponse(BaseModel):
    """工具列表响应"""
    tools: list[dict]


@router.post("/run")
async def agent_run(
    request: AgentRequest,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    同步执行 Agent ReAct 循环。

    前端发送一条自然语言指令，Agent 自主决定调用哪些工具，
    最终返回完整结果。

    示例: "帮我找最近 AI 领域的热点，生成一条口播文案"
    """
    executor = AgentExecutor(max_iterations=request.max_iterations)

    try:
        result = await executor.run(user_message=request.message, db=db)
        if result["success"]:
            return success_response(
                data={
                    "answer": result["answer"],
                    "iterations": result["iterations"],
                    "trace": result.get("trace", []),
                },
                message="Agent 执行完成",
            )
        else:
            return error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message=result.get("answer", "Agent 执行失败"),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    except Exception as e:
        logger.error(f"Agent 执行失败: {e}", exc_info=True)
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Agent 执行失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/stream")
async def agent_stream(
    request: AgentRequest,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    SSE 流式输出 Agent 思考过程。

    每完成一步（LLM 调用 / 工具执行）都推送一条事件：
    - thought: LLM 的思考过程
    - action: 工具调用
    - observation: 工具返回结果
    - answer: 最终答案
    """
    executor = AgentExecutor(max_iterations=request.max_iterations)

    async def event_generator():
        """生成 SSE 事件流"""
        try:
            # 发送工具列表
            yield f"data: {json.dumps({'type': 'tools', 'tools': [t.to_llm_schema() for t in tool_registry.list_tools()]}, ensure_ascii=False)}\n\n"

            # 发送用户指令
            yield f"data: {json.dumps({'type': 'thought', 'content': f'收到指令: {request.message}'}, ensure_ascii=False)}\n\n"

            # 复用 executor 的逻辑，但逐步推送
            from backend.core.ai_service import ai_manager
            from backend.services.agent_executor import _build_messages, _parse_step

            history = []
            trace = []

            for i in range(executor.max_iterations):
                messages = _build_messages(request.message, history)
                full_prompt = "\n\n".join(m["content"] for m in messages)

                # 流式调用 LLM
                llm_response = ""
                try:
                    async for chunk in ai_manager.generate_stream(full_prompt, max_tokens=2000):
                        llm_response += chunk
                        yield f"data: {json.dumps({'type': 'thought', 'content': chunk}, ensure_ascii=False)}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'content': f'LLM 调用失败: {e}'}, ensure_ascii=False)}\n\n"
                    break

                trace.append({"step": i + 1, "llm_response": llm_response})

                parsed = await _parse_step(llm_response)
                if parsed is None:
                    # 没有工具调用，直接结束
                    yield f"data: {json.dumps({'type': 'answer', 'content': llm_response.strip()}, ensure_ascii=False)}\n\n"
                    break

                action_type, payload = parsed

                if action_type == "answer":
                    yield f"data: {json.dumps({'type': 'answer', 'content': payload}, ensure_ascii=False)}\n\n"
                    break

                tool_name, args = payload
                tool = tool_registry.get(tool_name)

                yield f"data: {json.dumps({'type': 'action', 'tool': tool_name, 'arguments': args}, ensure_ascii=False)}\n\n"

                if tool is None:
                    observation = f"工具 '{tool_name}' 不存在。可用工具: {[t.name for t in tool_registry.list_tools()]}"
                else:
                    try:
                        result = await tool.execute(**args)
                        observation = json.dumps(result, ensure_ascii=False)
                    except Exception as e:
                        observation = f"工具执行出错: {e}"

                yield f"data: {json.dumps({'type': 'observation', 'content': observation}, ensure_ascii=False)}\n\n"

                history.append({"role": "assistant", "content": llm_response})
                history.append({"role": "user", "content": f"Observation: {observation}"})

            else:
                # 达到最大迭代次数
                yield f"data: {json.dumps({'type': 'thought', 'content': '达到最大步数，生成最终答案...'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Agent stream 异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/tools", response_model=ToolListResponse)
async def list_tools():
    """获取所有可用工具列表"""
    tools = [t.to_llm_schema() for t in tool_registry.list_tools()]
    return success_response(
        data={"tools": tools},
        message="获取工具列表成功",
    )
