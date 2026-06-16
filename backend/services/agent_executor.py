"""
Agent 执行器 — ReAct 循环

核心思路：
  Thought → Action(tool) → Observation → Thought → ... → Final Answer

LLM 被注入工具描述后，自行决定何时调用工具、如何组合结果。
"""
import json
import logging
import re
from typing import Optional

from backend.core.ai_service import ai_manager
from backend.services.agent_service import tool_registry

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5
FINISH_PATTERN = re.compile(r"(?:final.?answer|最终答案)\s*:?\s*(.*)", re.IGNORECASE | re.DOTALL)


def _build_messages(user_message: str, history: list[dict]) -> list[dict]:
    """构建发送给 LLM 的消息列表"""
    system_prompt = (
        "你是一个新媒体内容创作助手，名叫 MediaPilot Agent。"
        "你的目标是帮助用户完成内容创作相关任务。\n\n"
        "你有以下工具可用：\n"
        + tool_registry.to_system_prompt()
        + "\n\n"
        "工作流程：\n"
        "1. 分析用户需求，确定需要调用哪些工具\n"
        "2. 调用工具获取信息\n"
        "3. 根据工具返回结果决定下一步\n"
        "4. 重复直到完成任务\n"
        "5. 完成任务后，使用 'Final Answer:' 输出最终结果\n\n"
        "注意：\n"
        "- 每次只调用一个工具\n"
        "- 工具调用格式: Action: tool_name\\nAction Input: {\"key\": \"value\"}\n"
        "- 观察结果格式: Observation: <工具返回结果>\n"
        "- 最终答案格式: Final Answer: <你的回答>\n"
        "- 最多尝试 5 步，超过后直接给出最终答案\n"
        "- 用中文回答用户"
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


async def _parse_step(response: str) -> Optional[tuple[str, dict]]:
    """
    从 LLM 响应中解析工具调用或最终答案。

    返回:
        ("action", (tool_name, args)) — 需要调用工具
        ("answer", text) — 最终答案
        None — 无法解析，需要继续
    """
    # 尝试匹配最终答案
    match = FINISH_PATTERN.search(response)
    if match:
        return ("answer", match.group(1).strip())

    # 尝试匹配工具调用
    action_match = re.search(r"Action\s*:\s*(.+?)\s*\n", response, re.IGNORECASE)
    if not action_match:
        return None

    tool_name = action_match.group(1).strip()

    input_match = re.search(r"Action Input\s*:\s*(.+)", response, re.IGNORECASE | re.DOTALL)
    if not input_match:
        return ("answer", f"无法解析工具参数。工具: {tool_name}")

    try:
        args = json.loads(input_match.group(1).strip())
    except json.JSONDecodeError:
        return ("answer", f"工具参数 JSON 解析失败: {input_match.group(1).strip()}")

    return ("action", (tool_name, args))


class AgentExecutor:
    """ReAct Agent 执行器"""

    def __init__(self, max_iterations: int = MAX_ITERATIONS):
        self.max_iterations = max_iterations

    async def run(self, user_message: str, db: Optional[Any] = None) -> dict:
        """
        执行 ReAct 循环。

        Args:
            user_message: 用户自然语言指令
            db: 数据库会话（部分工具需要）

        Returns:
            {"success": bool, "answer": str, "iterations": int, "trace": [...]}
        """
        history: list[dict] = []
        trace: list[dict] = []

        for i in range(self.max_iterations):
            messages = _build_messages(user_message, history)

            try:
                response = await ai_manager.generate(
                    "\n\n".join(m["content"] for m in messages),
                    max_tokens=2000,
                )
            except Exception as e:
                logger.error(f"Agent LLM 调用失败: {e}")
                return {
                    "success": False,
                    "answer": f"AI 服务调用失败: {e}",
                    "iterations": i,
                    "trace": trace,
                }

            trace.append({"step": i + 1, "llm_response": response})
            logger.info(f"[Agent] Step {i + 1}: {response[:200]}")

            parsed = await _parse_step(response)
            if parsed is None:
                # 无法解析，当作最终答案
                return {
                    "success": True,
                    "answer": response.strip(),
                    "iterations": i + 1,
                    "trace": trace,
                }

            action_type, payload = parsed

            if action_type == "answer":
                return {
                    "success": True,
                    "answer": payload,
                    "iterations": i + 1,
                    "trace": trace,
                }

            # action_type == "action"
            tool_name, args = payload
            tool = tool_registry.get(tool_name)

            if tool is None:
                observation = f"工具 '{tool_name}' 不存在。可用工具: {[t.name for t in tool_registry.list_tools()]}"
            else:
                try:
                    result = await tool.execute(**args)
                    observation = json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    observation = f"工具执行出错: {e}"

            trace.append({
                "step": i + 1,
                "action": tool_name,
                "arguments": args,
                "observation": observation,
            })
            logger.info(f"[Agent] Tool: {tool_name} → {observation[:200]}")

            history.append({
                "role": "assistant",
                "content": response,
            })
            history.append({
                "role": "user",
                "content": f"Observation: {observation}",
            })

        # 达到最大迭代次数，强制给出最终答案
        history.append({
            "role": "user",
            "content": (
                "已达到最大步骤限制。请根据以上所有信息，给出最终答案。"
                "使用 'Final Answer:' 格式输出。"
            ),
        })

        try:
            messages = _build_messages(user_message, history)
            final_response = await ai_manager.generate(
                "\n\n".join(m["content"] for m in messages),
                max_tokens=2000,
            )
        except Exception as e:
            final_response = f"无法生成最终答案: {e}"

        trace.append({"step": "max_iterations", "forced_final": True})

        return {
            "success": True,
            "answer": final_response.strip(),
            "iterations": self.max_iterations,
            "trace": trace,
        }
