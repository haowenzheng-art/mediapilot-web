"""
口播文案生成服务
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import uuid
import asyncio
from datetime import datetime
from typing import Optional

from backend.core.ai_service import ai_manager
from backend.models.domain.persona import CopywritingGenerateRequest, CopywritingResponse

logger = logging.getLogger(__name__)


class CopywritingService:
    """口播文案生成服务"""

    def __init__(self):
        self._copywritings = {}  # 临时存储（生产环境应该存数据库）

    async def generate_async(self, request: CopywritingGenerateRequest) -> CopywritingResponse:
        """
        异步生成口播文案（支持爬取参考内容）

        Args:
            request: 生成请求

        Returns:
            生成的文案
        """
        copywriting_id = str(uuid.uuid4())

        # 获取参考内容（从0到1模式）
        reference_content = ""
        if request.mode == "from_zero" and request.topic:
            try:
                from backend.scrapers.content_reference_scraper import ContentReferenceScraper
                scraper = ContentReferenceScraper()
                results = await scraper.get_reference_content(
                    keyword=request.topic,
                    platforms=["weibo", "baidu", "zhihu"],
                    max_results=3
                )
                await scraper.close()

                if results.get("summary"):
                    reference_content = f"\n\n【参考内容】\n{results['summary']}"
                    logger.info(f"已获取{request.topic}的参考内容")
            except Exception as e:
                logger.warning(f"获取参考内容失败: {e}")

        # 构建AI提示词
        prompt = self._build_prompt(request, reference_content)

        # AI生成
        title = ""
        hooks = []
        content = ""

        if ai_manager.is_available():
            try:
                ai_result = ai_manager.generate(prompt, max_tokens=2000)
                parsed = self._parse_ai_result(ai_result)
                title = parsed.get("title", "")
                hooks = parsed.get("hooks", [])
                content = parsed.get("content", "")
            except Exception as e:
                logger.warning(f"AI生成失败: {e}")
                # 回退到mock
                pass

        # 如果AI生成失败或不可用，使用mock
        if not title:
            title, hooks, content = self._mock_generate(request)

        # 存储结果
        result = CopywritingResponse(
            id=copywriting_id,
            title=title,
            hooks=hooks,
            content=content,
            mode=request.mode,
            persona=request.persona,
            created_at=datetime.utcnow()
        )
        self._copywritings[copywriting_id] = result

        return result

    def generate(self, request: CopywritingGenerateRequest) -> CopywritingResponse:
        """
        生成口播文案

        Args:
            request: 生成请求

        Returns:
            生成的文案
        """
        copywriting_id = str(uuid.uuid4())

        # 构建AI提示词
        prompt = self._build_prompt(request)

        # AI生成
        title = ""
        hooks = []
        content = ""

        if ai_manager.is_available():
            try:
                ai_result = ai_manager.generate(prompt, max_tokens=2000)
                parsed = self._parse_ai_result(ai_result)
                title = parsed.get("title", "")
                hooks = parsed.get("hooks", [])
                content = parsed.get("content", "")
            except Exception as e:
                logger.warning(f"AI生成失败: {e}")
                # 回退到mock
                pass

        # 如果AI生成失败或不可用，使用mock
        if not title:
            title, hooks, content = self._mock_generate(request)

        # 存储结果
        result = CopywritingResponse(
            id=copywriting_id,
            title=title,
            hooks=hooks,
            content=content,
            mode=request.mode,
            persona=request.persona,
            created_at=datetime.utcnow()
        )
        self._copywritings[copywriting_id] = result

        return result

    def rewrite(self, copywriting_id: str, direction: str, persona: str) -> CopywritingResponse:
        """
        改写文案（再改改功能）

        Args:
            copywriting_id: 文案ID
            direction: 改写方向 (more_colloquial/add_emotion/add_opinion)
            persona: 人设

        Returns:
            改写后的文案
        """
        original = self._copywritings.get(copywriting_id)
        if not original:
            raise ValueError("文案不存在")

        # 构建改写提示词
        direction_map = {
            "more_colloquial": "更口语化",
            "add_emotion": "加情绪",
            "add_opinion": "加观点"
        }
        direction_text = direction_map.get(direction, direction)

        prompt = f"""你是一位{persona}。

请将以下口播文案进行改写，要求：{direction_text}

【原文】
标题：{original.title}
内容：{original.content}

【改写要求】
- 保持原文的核心信息和结构
- 根据人设{persona}的视角进行改写
- {direction_text}，让内容更有感染力
- 禁止使用"#"符号
- 格式工整

【输出格式】
标题：xxx

钩子（2-3个备选）：
1. xxx
2. xxx

文案正文：
xxx
"""

        # AI改写
        title = ""
        hooks = []
        content = ""

        if ai_manager.is_available():
            try:
                ai_result = ai_manager.generate(prompt, max_tokens=2000)
                parsed = self._parse_ai_result(ai_result)
                title = parsed.get("title", "")
                hooks = parsed.get("hooks", [])
                content = parsed.get("content", "")
            except Exception as e:
                logger.warning(f"AI改写失败: {e}")

        # 如果AI改写失败，简单修改
        if not title:
            title = f"{original.title}（{direction_text}）"
            hooks = original.hooks
            content = f"【{direction_text}版本】\n{original.content}"

        result = CopywritingResponse(
            id=str(uuid.uuid4()),
            title=title,
            hooks=hooks,
            content=content,
            mode=original.mode,
            persona=persona,
            created_at=datetime.utcnow()
        )

        return result

    def _build_prompt(self, request: CopywritingGenerateRequest, reference_content: str = "") -> str:
        """构建AI生成提示词"""
        base_prompt = f"""你是一位{request.persona}。

请根据以下要求创作口播文案。

【写作要求】
- 语气像一个幽默风趣、干货满满的老师
- 有趣的科普风格，轻松但有价值
- 禁止使用"#"符号
- 格式工整
- 去除AI感，不要使用"本文""文章""综上所述"等表达

【输出格式】
标题：xxx

钩子（2-3个备选）：
1. xxx
2. xxx

文案正文：
xxx
"""

        if request.mode == "from_zero":
            return f"""{base_prompt}

【话题】
{request.topic}
{reference_content}

请基于以上话题和参考内容，创作符合人设{request.persona}视角的口播文案。
"""

        elif request.mode == "hotspot":
            return f"""{base_prompt}

【热点内容框架】
{request.hotspot_content}
{reference_content}

请基于以上热点内容框架和参考内容，创作符合人设{request.persona}视角的口播文案。
"""

        elif request.mode == "rewrite":
            return f"""{base_prompt}

【原文】
{request.original_text}
{reference_content}

请对以上原文进行洗稿重写，以{request.persona}的视角重新表达，保持核心信息但换种说法。
"""

        return base_prompt

    def _parse_ai_result(self, ai_result: str) -> dict:
        """解析AI生成结果"""
        result = {"title": "", "hooks": [], "content": ""}

        lines = ai_result.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 移除#号（AI可能误加）
            line = line.replace("#", "").strip()

            if line.startswith("标题："):
                result["title"] = line.replace("标题：", "").strip()
            elif line.startswith("钩子"):
                current_section = "hooks"
            elif line.startswith("文案正文") or line.startswith("正文"):
                current_section = "content"
            elif current_section == "hooks":
                # 提取钩子：1. xxx 或 xxx
                hook = line
                if hook.startswith(("1.", "2.", "3.")):
                    hook = hook.split(".", 1)[1].strip()
                result["hooks"].append(hook)
            elif current_section == "content":
                result["content"] += line + "\n"

        # 清理
        result["content"] = result["content"].strip()

        # 如果解析失败，简单处理
        if not result["title"] and not result["content"]:
            # 尝试直接使用AI结果作为内容
            result["content"] = ai_result.replace("#", "").strip()
            result["title"] = "口播文案"

        return result

    def _mock_generate(self, request: CopywritingGenerateRequest) -> tuple:
        """Mock生成（用于开发测试）"""
        if request.mode == "from_zero":
            topic = request.topic or "未指定话题"
            return (
                f"关于{topic}的那些事",
                [
                    f"关于{topic}，90%的人都不知道",
                    f"3分钟带你了解{topic}的真相",
                    f"{topic}到底是什么？今天聊聊"
                ],
                f"""今天来聊聊{topic}这个话题。

作为一个{request.persona}，我注意到很多人对{topic}有一些误解。

首先，{topic}其实没那么复杂。核心就3个关键点：

第一点，了解基础知识。很多人一上来就想一步到位，结果走弯路。

第二点，要实践。光看理论没用，动手做才知道问题在哪。

第三点，持续优化。第一次做得不好很正常，慢慢调整。

记住，{topic}不是终点，是工具。关键是用它解决问题。

下期我们深入聊聊{topic}的进阶用法，记得点赞关注。"""
            )

        elif request.mode == "hotspot":
            return (
                "热点解读",
                [
                    "今天这个热点很有意思",
                    "为什么这件事这么火？",
                    "别急，3分钟给你讲明白"
                ],
                f"""刚刚看到这个热点，作为一个{request.persona}，有一些想法。

简单说下情况：{request.hotspot_content[:50]}...

这事儿为什么火？因为...

给大家几点建议：

第一，理性看待。网络信息真假混杂。

第二，关注核心。别被情绪带偏。

第三，思考背后的原因。

好了，今天就聊到这。下期见！"""
            )

        else:  # rewrite
            return (
                "改写版文案",
                [
                    "这个话题很有意思",
                    "今天聊聊这件事",
                    "别急，听我慢慢说"
                ],
                f"""作为一个{request.persona}，我对这个话题有一些看法。

{request.original_text[:100]}...

总的来说，这就是我想表达的。

如果有不同意见，欢迎在评论区讨论。记得点赞关注，下期更精彩。"""
            )

    def get_copywriting(self, copywriting_id: str) -> Optional[CopywritingResponse]:
        """获取文案"""
        return self._copywritings.get(copywriting_id)


# 全局实例
copywriting_service = CopywritingService()
