"""
内容生成领域模型
"""
from typing import List, Optional


class Shot:
    """分镜头"""

    def __init__(
        self,
        scene: int,
        duration: str,
        visual: str,
        audio: str,
        notes: Optional[str] = None,
    ):
        self.scene = scene
        self.duration = duration
        self.visual = visual
        self.audio = audio
        self.notes = notes

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "scene": self.scene,
            "duration": self.duration,
            "visual": self.visual,
            "audio": self.audio,
            "notes": self.notes,
        }


class Copywriting:
    """文案"""

    def __init__(
        self,
        title: str,
        hooks: List[str],
        call_to_action: str,
        tags: List[str],
    ):
        self.title = title
        self.hooks = hooks
        self.call_to_action = call_to_action
        self.tags = tags

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "hooks": self.hooks,
            "call_to_action": self.call_to_action,
            "tags": self.tags,
        }
