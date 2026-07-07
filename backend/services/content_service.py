"""
内容生成业务逻辑
"""
from backend.models.schemas.response import (
    Shot,
    Copywriting,
    ContentGenerateResponse,
    APIResponse,
)
from backend.core.ai_service import ai_manager


def _normalize_shot(s: dict) -> dict:
    """容错 AI / mock 输出：scene int→str，duration str "MM:SS-MM:SS" → float 秒数（取 end）

    AI prompt 让 AI 输出 scene=int（镜头号）和 duration="MM:SS-MM:SS"（区间），
    但 Shot schema 期望 scene=str（场景描述）和 duration=Optional[float]（秒数）。
    Pydantic v2 默认严格校验会抛 ValidationError，这里做兼容转换。
    """
    s = dict(s)  # 不改原 dict
    if isinstance(s.get("scene"), int):
        s["scene"] = str(s["scene"])
    if isinstance(s.get("duration"), str):
        d = s["duration"].strip()
        if "-" in d:
            end = d.split("-")[-1].strip()
            try:
                m, sec = end.split(":")
                s["duration"] = int(m) * 60 + int(sec)
            except (ValueError, IndexError):
                s["duration"] = None
        else:
            try:
                s["duration"] = float(d)
            except ValueError:
                s["duration"] = None
    return s


def _normalize_copywriting(c: dict, topic: str, platform: str) -> dict:
    """容错 AI / mock 输出：Copywriting 字段补齐

    AI prompt 输出 copywriting 的字段是 title/hooks/call_to_action/tags，
    但 Copywriting schema 要求 platform/topic/script。补齐缺失字段。
    """
    c = dict(c)
    c.setdefault("platform", platform)
    c.setdefault("topic", topic)
    # AI prompt 没 script 字段 → 复用 title 当 script（避免空字符串触发必填校验）
    c.setdefault("script", c.get("title", ""))
    # AI 用 call_to_action，schema 用 cta
    if "call_to_action" in c and "cta" not in c:
        c["cta"] = c["call_to_action"]
    return c


class ContentService:
    """内容生成服务"""

    def __init__(self):
        pass

    async def generate_script(
        self,
        topic: str,
        platform: str,
        duration: int,
        style: str
    ) -> ContentGenerateResponse:
        """
        生成分镜头脚本和文案

        Args:
            topic: 选题
            platform: 平台
            duration: 视频时长
            style: 风格

        Returns:
            内容生成响应
        """
        # 检查 AI 服务是否可用
        if not ai_manager.get_current_service() or not ai_manager.get_current_service().is_available():
            # 返回模拟数据
            mock_script = [
                {
                    "scene": 1,
                    "duration": "0:00-0:05",
                    "visual": "开头吸引眼球",
                    "audio": "大家好",
                    "notes": "要有冲击力"
                },
                {
                    "scene": 2,
                    "duration": "0:05-0:15",
                    "visual": "展示主题",
                    "audio": f"今天我们来聊{topic}",
                    "notes": ""
                },
                {
                    "scene": 3,
                    "duration": "0:15-0:30",
                    "visual": "详细讲解",
                    "audio": "具体内容...",
                    "notes": "配合图表"
                },
                {
                    "scene": 4,
                    "duration": "0:30-0:45",
                    "visual": "总结升华",
                    "audio": "希望对你有帮助",
                    "notes": ""
                },
                {
                    "scene": 5,
                    "duration": "0:45-0:60",
                    "visual": "引导关注",
                    "audio": "点赞关注",
                    "notes": "强调CTA"
                }
            ]
            mock_copy = {
                "title": f"{topic}爆款标题",
                "hooks": ["你还不知道的秘密！", "90%的人都做错了", "建议收藏！"],
                "call_to_action": "点赞关注，下期更精彩！",
                "tags": [f"#{topic}", "#新媒体", "#干货"]
            }
            return ContentGenerateResponse(
                topic=topic,
                script=[Shot(**_normalize_shot(s)) for s in mock_script],
                copywriting=Copywriting(**_normalize_copywriting(mock_copy, topic, platform))
            )

        # 使用 AI 生成
        result = await ai_manager.generate_content_script(
            topic,
            platform,
            duration,
            style
        )

        script = [Shot(**_normalize_shot(s)) for s in result.get("script", [])]
        copywriting = Copywriting(**_normalize_copywriting(result.get("copywriting", {}), topic, platform))

        return ContentGenerateResponse(
            topic=topic,
            script=script,
            copywriting=copywriting
        )

    async def rewrite_transcript(
        self,
        transcript: str,
        style: str,
        target_duration: int
    ) -> dict:
        """
        改写逐字稿

        Args:
            transcript: 原逐字稿
            style: 目标风格
            target_duration: 目标时长

        Returns:
            改写后的文本
        """
        # 检查 AI 服务是否可用
        if not ai_manager.get_current_service() or not ai_manager.get_current_service().is_available():
            return None

        rewritten = await ai_manager.rewrite_transcript(
            transcript,
            style,
            target_duration
        )

        return {"rewritten_text": rewritten}
