"""
Agent 服务模块 — Tool 抽象层 + 具体工具实现
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.services.trending_service import TrendingService
from backend.services.copywriting_service import copywriting_service
from backend.services.content_library_service import content_library_service
from backend.models.domain.persona import CopywritingGenerateRequest
from backend.models.domain.content_library import ContentCreate, ContentType

logger = logging.getLogger(__name__)


# ==================== Tool 基类 ====================

class Tool(ABC):
    """所有 Agent 工具的抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一名称，LLM 通过此名称调用"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """给 LLM 看的自然语言描述，说明工具用途"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        JSON Schema 格式的参数定义。
        LLM 据此生成调用参数。
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> dict:
        """
        执行工具逻辑。
        返回 {"success": bool, "data": ..., "error": ...}
        """
        pass

    def to_llm_schema(self) -> dict:
        """转换为 LLM function-calling / tool-use 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


# ==================== ToolRegistry ====================

class ToolRegistry:
    """工具注册表 — 集中管理所有可用工具"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> "ToolRegistry":
        """注册一个工具（支持链式调用）"""
        self._tools[tool.name] = tool
        logger.info(f"Tool 已注册: {tool.name}")
        return self

    def get(self, name: str) -> Optional[Tool]:
        """按名称获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """返回所有已注册工具"""
        return list(self._tools.values())

    def list_llm_schemas(self) -> list[dict]:
        """返回所有工具的 LLM schema（用于注入 system prompt）"""
        return [t.to_llm_schema() for t in self._tools.values()]

    def to_system_prompt(self) -> str:
        """生成供 LLM 使用的系统提示文本"""
        schemas = self.list_llm_schemas()
        if not schemas:
            return "你没有任何可用的工具。"
        parts = ["你可以使用以下工具完成任务："]
        for s in schemas:
            parts.append(f"- {s['name']}: {s['description']}")
            parts.append(f"  参数格式: {json.dumps(s['parameters'], ensure_ascii=False)}")
        parts.append("调用格式: 使用工具名并传入参数字典，例如 {'tool': 'tool_name', 'arguments': {...}}")
        return "\n".join(parts)


# 全局注册表实例
tool_registry = ToolRegistry()


# ==================== 具体 Tool 实现 ====================

class SearchHotspotsTool(Tool):
    """搜索全网热点话题"""

    @property
    def name(self) -> str:
        return "search_hotspots"

    @property
    def description(self) -> str:
        return (
            "搜索全网热点话题。根据关键词在多个社交平台（抖音、微博、小红书、百度、知乎）搜索近期热点新闻，"
            "返回标题、热度、来源和摘要。适合用于发现创作素材。"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词，例如 'AI'、'新能源汽车'"
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "平台列表，可选值: douyin, weibo, xiaohongshu, baidu, zhihu",
                    "default": ["douyin", "weibo", "xiaohongshu"]
                },
                "days": {
                    "type": "integer",
                    "description": "搜索时间范围（天数），1-30",
                    "default": 7
                }
            },
            "required": ["keyword"]
        }

    async def execute(self, keyword: str, platforms: Optional[list] = None, days: int = 7) -> dict:
        try:
            service = TrendingService()
            result = await service.search(
                keyword=keyword,
                platforms=platforms or ["douyin", "weibo", "xiaohongshu"],
                days=days
            )
            topics = [
                {
                    "title": t.title,
                    "source": t.source,
                    "heat_value": t.heat_value,
                    "summary": t.summary or "",
                    "trend_direction": t.trend_direction,
                }
                for t in result.hot_topics
            ]
            return {
                "success": True,
                "data": {
                    "keyword": keyword,
                    "total_count": result.total_count,
                    "hot_topics": topics,
                },
            }
        except Exception as e:
            logger.error(f"SearchHotspotsTool 执行失败: {e}")
            return {"success": False, "error": str(e)}


class GenerateCopywritingTool(Tool):
    """生成口播文案"""

    @property
    def name(self) -> str:
        return "generate_copywriting"

    @property
    def description(self) -> str:
        return (
            "根据人设和话题生成口播文案。支持三种模式：from_zero（从0到1创作）、"
            "hotspot（基于热点框架）、rewrite（改写已有文案）。"
            "输出包含标题、钩子和正文。"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["from_zero", "hotspot", "rewrite"],
                    "description": "生成模式"
                },
                "persona": {
                    "type": "string",
                    "description": "人设描述，例如 '科技博主'、'育儿专家'"
                },
                "topic": {
                    "type": "string",
                    "description": "话题内容（from_zero 模式需要）"
                },
                "hotspot_content": {
                    "type": "string",
                    "description": "热点内容框架（hotspot 模式需要）"
                },
                "original_text": {
                    "type": "string",
                    "description": "原文（rewrite 模式需要）"
                }
            },
            "required": ["mode", "persona"]
        }

    async def execute(
        self,
        mode: str,
        persona: str,
        topic: Optional[str] = None,
        hotspot_content: Optional[str] = None,
        original_text: Optional[str] = None,
    ) -> dict:
        try:
            req = CopywritingGenerateRequest(
                mode=mode,
                persona=persona,
                topic=topic,
                hotspot_content=hotspot_content,
                original_text=original_text,
            )
            # 使用 db_session 上下文（Agent 场景下无持久 DB，使用内存回退）
            result = await copywriting_service.generate(req, db=None)
            return {
                "success": True,
                "data": {
                    "id": result.id,
                    "title": result.title,
                    "hooks": result.hooks,
                    "content": result.content,
                    "mode": result.mode,
                },
            }
        except Exception as e:
            logger.error(f"GenerateCopywritingTool 执行失败: {e}")
            return {"success": False, "error": str(e)}


class GetContentLibraryTool(Tool):
    """查询内容库"""

    @property
    def name(self) -> str:
        return "get_content_library"

    @property
    def description(self) -> str:
        return (
            "查询内容库中已有的文案或脚本。可按内容类型、是否处理状态筛选，"
            "返回标题、摘要、平台和创建时间。适合在创作前查看历史内容。"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "content_type": {
                    "type": "string",
                    "enum": ["copywriting", "shoot_script"],
                    "description": "内容类型"
                },
                "is_processed": {
                    "type": "boolean",
                    "description": "是否已处理"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量上限",
                    "default": 20
                },
                "offset": {
                    "type": "integer",
                    "description": "偏移量（分页）",
                    "default": 0
                }
            },
            "required": []
        }

    async def execute(
        self,
        content_type: Optional[str] = None,
        is_processed: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        try:
            from backend.models.domain.content_library import ContentType
            ct = ContentType(content_type) if content_type else None

            # Agent 场景下可能没有 DB session，返回空列表
            db = None
            contents = []
            try:
                from backend.config.database import SessionLocal
                db = SessionLocal()
                contents = content_library_service.get_user_contents(
                    db=db,
                    user_id=0,  # agent 场景
                    content_type=ct,
                    is_processed=is_processed,
                    limit=limit,
                    offset=offset,
                )
            except Exception:
                pass
            finally:
                if db:
                    db.close()

            items = [
                {
                    "id": c.id,
                    "content_id": c.content_id,
                    "title": c.title,
                    "summary": c.summary or "",
                    "content_type": c.content_type.value,
                    "platform": c.platform,
                    "is_processed": c.is_processed,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in contents
            ]
            return {
                "success": True,
                "data": {"contents": items, "total": len(items)},
            }
        except Exception as e:
            logger.error(f"GetContentLibraryTool 执行失败: {e}")
            return {"success": False, "error": str(e)}


# ==================== 注册所有工具 ====================

tool_registry.register(SearchHotspotsTool())
tool_registry.register(GenerateCopywritingTool())
tool_registry.register(GetContentLibraryTool())
