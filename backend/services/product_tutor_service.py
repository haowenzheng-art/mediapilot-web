"""
产品教程 (Product Tutor)
- 加载 backend/data/product_kb.yaml，关键词匹配命中常见问题
- 命中：直接返回 KB 答案 + 可选跳转动作（不调 LLM）
- 未命中：把 KB 摘要拼进系统提示，调 ai_manager 走兜底（若可用），否则提示"问题不在覆盖范围"
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

import yaml

logger = logging.getLogger(__name__)

_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "product_kb.yaml"


@dataclass
class FAQEntry:
    id: str
    question: str
    keywords: List[str]
    answer: str
    action_url: Optional[str] = None
    action_text: Optional[str] = None


@dataclass
class TutorReply:
    matched: bool
    source: str            # "kb" | "llm" | "fallback"
    faq_id: Optional[str]
    answer: str
    action_url: Optional[str] = None
    action_text: Optional[str] = None


class ProductTutorService:
    def __init__(self, kb_path: Path = _KB_PATH):
        self.kb_path = kb_path
        self._faqs: List[FAQEntry] = []
        self._load()

    def _load(self):
        if not self.kb_path.exists():
            logger.warning(f"产品知识库不存在: {self.kb_path}")
            return
        with open(self.kb_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for item in data.get("faqs", []):
            self._faqs.append(FAQEntry(
                id=item["id"],
                question=item["question"],
                keywords=[k.lower() for k in item.get("keywords", [])],
                answer=item["answer"].strip(),
                action_url=item.get("action_url"),
                action_text=item.get("action_text"),
            ))
        logger.info(f"产品知识库加载完成: {len(self._faqs)} 条 FAQ")

    @property
    def faqs(self) -> List[FAQEntry]:
        return self._faqs

    def _normalize(self, text: str) -> str:
        return re.sub(r"[\s,。？！?,.!;；:：]+", " ", text.lower()).strip()

    def match(self, query: str) -> Optional[FAQEntry]:
        """关键词匹配——任一关键词命中即视为匹配，命中最多关键词的 FAQ 胜出"""
        norm = self._normalize(query)
        if not norm:
            return None
        best: Optional[FAQEntry] = None
        best_score = 0
        for faq in self._faqs:
            score = sum(1 for kw in faq.keywords if kw in norm)
            if score > best_score:
                best, best_score = faq, score
        return best if best_score > 0 else None

    async def ask(self, query: str) -> TutorReply:
        faq = self.match(query)
        if faq:
            return TutorReply(
                matched=True,
                source="kb",
                faq_id=faq.id,
                answer=faq.answer,
                action_url=faq.action_url,
                action_text=faq.action_text,
            )

        # 未命中 — 尝试调 ai_manager 兜底（带上 KB 摘要做 RAG）
        from backend.core.ai_service import ai_manager
        if ai_manager.is_available():
            try:
                kb_summary = "\n".join(
                    f"- {f.question}: {f.answer.splitlines()[0]}" for f in self._faqs
                )
                prompt = (
                    "你是 MediaPilot 产品教程助手。基于下列功能清单，用一两句中文回答用户的问题；"
                    "如果问题不在功能清单内，直接告知用户当前产品不支持此功能。请勿编造不存在的功能。\n\n"
                    f"功能清单：\n{kb_summary}\n\n"
                    f"用户问题：{query}\n"
                    "回答："
                )
                answer = await ai_manager.generate(prompt, max_tokens=300)
                return TutorReply(
                    matched=False, source="llm", faq_id=None,
                    answer=answer.strip(),
                )
            except Exception as e:
                logger.warning(f"LLM 兜底失败: {e}")

        return TutorReply(
            matched=False, source="fallback", faq_id=None,
            answer="抱歉，这个问题暂时不在产品教程的覆盖范围。可以试着问：怎么搜热点？怎么生成口播文案？怎么订阅话题？",
        )


product_tutor_service = ProductTutorService()
