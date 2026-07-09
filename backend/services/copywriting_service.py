"""
口播文案生成服务
"""
import logging
import uuid
import asyncio
from datetime import datetime
from typing import Optional, AsyncGenerator, Dict, Any

from sqlalchemy.orm import Session

from backend.core.ai_service import ai_manager
from backend.models.domain.persona import CopywritingGenerateRequest, CopywritingResponse
from backend.repository.copywriting_repo import CopywritingRepository

logger = logging.getLogger(__name__)


class CopywritingService:
    """口播文案生成服务"""

    def __init__(self):
        self._repo: Optional[CopywritingRepository] = None

    def _get_repo(self, db: Session) -> CopywritingRepository:
        if self._repo is None or self._repo.db != db:
            self._repo = CopywritingRepository(db)
        return self._repo

    async def generate(self, request: CopywritingGenerateRequest, db: Session, user_id: int) -> CopywritingResponse:
        """异步生成口播文案（支持爬取参考内容）"""
        copywriting_id = str(uuid.uuid4())

        # 获取参考内容（从0到1模式）
        reference_content = ""
        if request.mode == "from_zero" and request.topic:
            try:
                from backend.scrapers.content_reference_scraper import ContentReferenceScraper
                scraper = ContentReferenceScraper()
                results = await scraper.get_reference_content(
                    keyword=request.topic,
                    platforms=["baidu", "toutiao"],  # v4 精简：下线的 4 源不在参考里
                    max_results=3
                )
                await scraper.close()

                if results.get("summary"):
                    reference_content = f"\n\n【参考内容】\n{results['summary']}"
                    logger.info(f"已获取{request.topic}的参考内容")
            except Exception as e:
                logger.warning(f"获取参考内容失败: {e}")

        prompt = self._build_prompt(request, reference_content)
        title, hooks, content = await self._ai_generate_or_mock(prompt, request)

        result = CopywritingResponse(
            id=copywriting_id,
            title=title,
            hooks=hooks,
            content=content,
            mode=request.mode,
            persona=request.persona,
            created_at=datetime.utcnow()
        )

        # 持久化到数据库
        repo = self._get_repo(db)
        repo.create(
            copywriting_id=copywriting_id,
            title=title,
            hooks=hooks,
            content=content,
            mode=request.mode,
            persona=request.persona,
            user_id=user_id
        )

        return result

    async def generate_stream(
        self,
        request: CopywritingGenerateRequest,
        db: Session,
        user_id: int,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式生成口播文案（SSE 端点配套）。

        yield 事件对象：
          {"type": "content", "delta": "..."}    AI 输出片段（content）
          {"type": "reasoning", "delta": "..."}  AI 输出片段（reasoning）
          {"type": "meta", "meta": {"final": true, "parsed": {...}}}  结束事件，带解析结果
          {"type": "error", "delta": "..."}      错误
        """
        # 复用 reference_content 拉取逻辑（from_zero 模式）
        reference_content = ""
        if request.mode == "from_zero" and request.topic:
            try:
                from backend.scrapers.content_reference_scraper import ContentReferenceScraper
                scraper = ContentReferenceScraper()
                results = await scraper.get_reference_content(
                    keyword=request.topic,
                    platforms=["baidu", "toutiao"],  # v4 精简：下线的 4 源不在参考里
                    max_results=3
                )
                await scraper.close()

                if results.get("summary"):
                    reference_content = f"\n\n【参考内容】\n{results['summary']}"
                    logger.info(f"已获取{request.topic}的参考内容")
            except Exception as e:
                logger.warning(f"获取参考内容失败: {e}")

        prompt = self._build_prompt(request, reference_content)

        if not ai_manager.is_available():
            yield {"type": "error", "delta": "AI 服务未配置或不可用，无法生成文案"}
            return

        accumulated_content = ""
        reasoning_seen = False
        try:
            async for event in ai_manager.generate_stream(
                prompt,
                max_tokens=2000,
                enable_reasoning=request.enable_reasoning,
            ):
                if event.get("type") == "content" and event.get("delta"):
                    accumulated_content += event["delta"]
                    yield event
                elif event.get("type") == "reasoning" and event.get("delta"):
                    reasoning_seen = True
                    yield event
                elif event.get("type") == "error":
                    yield event
                    return
        except Exception as e:
            logger.error(f"AI 流式生成失败: {e}")
            yield {"type": "error", "delta": f"AI 生成失败: {e}"}
            return

        # 解析累积内容
        parsed = self._parse_ai_result(accumulated_content)
        title = parsed.get("title", "")
        hooks = parsed.get("hooks", [])
        content = parsed.get("content", "")

        if not title and not content:
            yield {"type": "error", "delta": "AI 返回为空，请稍后重试"}
            return

        # 持久化
        copywriting_id = str(uuid.uuid4())
        repo = self._get_repo(db)
        repo.create(
            copywriting_id=copywriting_id,
            title=title,
            hooks=hooks,
            content=content,
            mode=request.mode,
            persona=request.persona,
            user_id=user_id
        )

        logger.info(
            f"AI 流式生成完成 mode={request.mode} title_len={len(title)} "
            f"content_len={len(content)} reasoning_seen={reasoning_seen}"
        )

        # 发送最终 meta 事件
        yield {
            "type": "meta",
            "meta": {
                "final": True,
                "reasoning_supported": reasoning_seen,
                "parsed": {
                    "id": copywriting_id,
                    "title": title,
                    "hooks": hooks,
                    "content": content,
                    "mode": request.mode,
                    "persona": request.persona,
                },
            },
        }

    async def rewrite(self, copywriting_id: str, direction: str, persona: str, db: Session) -> CopywritingResponse:
        """改写文案（再改改功能，异步）"""
        repo = self._get_repo(db)
        original = repo.get_by_id(copywriting_id)
        if not original:
            raise ValueError("文案不存在")

        direction_map = {
            "more_colloquial": "更口语化",
            "add_emotion": "加情绪",
            "add_opinion": "加观点"
        }
        direction_text = direction_map.get(direction, direction)

        prompt = f"""你是{persona}，正在改写一条已有的口播文案。

【改写方向】{direction_text}

【原文】
标题：{original.title}
内容：{original.content}

【改写硬要求】
1. 打破原文结构：重新组织段落顺序 / 拆分合并句子 / 换开头/换钩子，不要"换皮重排"
2. 人设一致性：语气、词汇、句式必须明显贴近{persona}（不只是改个称呼）
3. 保留核心信息：原文的关键论点 / 数据 / 案例不能丢
4. 口语化硬约束（详见下方）

【口语化硬约束】
- 短句为主，单句 ≤ 25 字
- 禁用"大家好/今天我们来/接下来"开场
- 段落过渡用"说回来/讲到这儿/对了"
- 禁用书面词："本文""文章""综上所述""首先/其次/最后"
- 结尾强引导：抛问题/争议/悬念，不写"记得点赞关注"
- 禁止使用"#"符号

【输出格式】
标题：xxx

钩子（2-3个备选）：
1. xxx
2. xxx

文案正文：
xxx
"""

        title, hooks, content = await self._ai_rewrite_or_mock(prompt, original, direction_text)

        result = CopywritingResponse(
            id=str(uuid.uuid4()),
            title=title,
            hooks=hooks,
            content=content,
            mode=original.mode or "rewrite",
            persona=persona,
            created_at=datetime.utcnow()
        )

        # 保存改写结果
        repo.create(
            copywriting_id=result.id,
            title=title,
            hooks=hooks,
            content=content,
            mode=original.mode or "rewrite",
            persona=persona,
            user_id=original.user_id
        )

        return result

    async def get_copywriting(self, copywriting_id: str, db: Session) -> Optional[CopywritingResponse]:
        """从数据库获取文案（同步，不经过 AI）"""
        repo = self._get_repo(db)
        cw = repo.get_by_id(copywriting_id)
        if cw:
            return CopywritingResponse(
                id=cw.copywriting_id,
                title=cw.title,
                hooks=cw.hooks or [],
                content=cw.content or "",
                mode=cw.mode or "",
                persona=cw.persona or "",
                created_at=cw.created_at or datetime.utcnow()
            )
        return None

    async def _ai_generate_or_mock(self, prompt: str, request: CopywritingGenerateRequest) -> tuple:
        """AI 生成（生产路径）

        AI 不可用或失败时抛 RuntimeError，让上层返回明确错误。
        测试环境可设 settings.USE_MOCK_AI=True 走 _mock_generate 兜底。
        生产保持 False —— 之前 mock 会返回 "X运营技巧" 这类模板假数据污染用户内容。
        """
        if not ai_manager.is_available():
            from backend.config.settings import settings
            if not settings.USE_MOCK_AI:
                raise RuntimeError("AI 服务未配置或不可用，无法生成文案")
            logger.info("USE_MOCK_AI=True，走 mock 生成")
            return self._mock_generate(request)
        ai_result = await ai_manager.generate(prompt, max_tokens=2000)
        parsed = self._parse_ai_result(ai_result)
        title = parsed.get("title", "")
        hooks = parsed.get("hooks", [])
        content = parsed.get("content", "")
        if not title and not content:
            raise RuntimeError("AI 返回为空，请稍后重试")
        logger.info(f"AI 生成完成 mode={request.mode} title_len={len(title)} content_len={len(content)}")
        return title, hooks, content

    async def _ai_rewrite_or_mock(self, prompt: str, original, direction_text: str) -> tuple:
        """改写时的 AI 生成（生产路径）

        失败时直接抛错。改写有原文托底，不需要 mock 模板。
        """
        if not ai_manager.is_available():
            raise RuntimeError("AI 服务未配置或不可用，无法改写")
        ai_result = await ai_manager.generate(prompt, max_tokens=2000)
        parsed = self._parse_ai_result(ai_result)
        title = parsed.get("title", "")
        hooks = parsed.get("hooks", [])
        content = parsed.get("content", "")
        if not title and not content:
            raise RuntimeError("AI 返回为空，请稍后重试")
        logger.info(f"AI 改写完成 direction={direction_text} title_len={len(title)}")
        return title, hooks, content

    def _build_prompt(self, request: CopywritingGenerateRequest, reference_content: str = "") -> str:
        """构建AI生成提示词

        口语化硬约束（v4 D 任务强化）：
        - 短句为主，单句 ≤ 25 字
        - 禁用书面连接词（然而/因此/综上所述）
        - 禁用"大家好/今天我们来/接下来"等AI开场套话
        - 段落过渡用口语词（说回来/讲到这儿/对了）
        - 结尾强引导（抛问题/争议/悬念），不写"记得点赞关注"套话
        """
        base_prompt = f"""你是{request.persona}，正在拍一条短视频口播。

【写作要求 — 口语化硬约束】
1. 像在跟朋友聊天：短句为主，单句尽量 ≤ 25 字；忌长句堆砌
2. 开头禁用："大家好""今天我们来聊聊""接下来""在当今社会"
   ✅ 改用："老铁们""家人们""各位""说真的""讲真"
3. 段落过渡用口语词："说回来""讲到这儿""对了""说白了"
   ❌ 禁用："然而""因此""综上所述""首先/其次/最后"
4. 禁用书面词："本文""文章""论述""阐明""深刻"
5. 结尾强引导：抛一个让观众忍不住评论的问题 / 抖个争议点 / 留个悬念
   ❌ 禁用："记得点赞关注""下期更精彩""我们下期再见"
6. 禁止使用"#"符号
7. 格式工整：标题 + 钩子 + 正文清晰分段

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
            line = line.replace("#", "").strip()

            if line.startswith("标题："):
                result["title"] = line.replace("标题：", "").strip()
            elif line.startswith("钩子"):
                current_section = "hooks"
            elif line.startswith("文案正文") or line.startswith("正文"):
                current_section = "content"
            elif current_section == "hooks":
                hook = line
                if hook.startswith(("1.", "2.", "3.")):
                    hook = hook.split(".", 1)[1].strip()
                result["hooks"].append(hook)
            elif current_section == "content":
                result["content"] += line + "\n"

        result["content"] = result["content"].strip()

        if not result["title"] and not result["content"]:
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
        else:
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


# 全局实例
copywriting_service = CopywritingService()
