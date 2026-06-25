"""
拍摄脚本相关的领域模型
定义请求和响应的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PlatformType(str, Enum):
    """平台类型"""
    DOUYIN = "douyin"  # 抖音竖屏 60s
    XIAOHONGSHU = "xiaohongshu"  # 小红书 3min
    BILIBILI = "bilibili"  # B站横屏 5-10min


class ScriptStyle(str, Enum):
    """脚本风格"""
    ENERGETIC = "energetic"  # 激情热血
    RELAXED = "relaxed"  # 轻松幽默
    PROFESSIONAL = "professional"  # 专业分析


class Shot(BaseModel):
    """分镜头"""
    shot_number: int = Field(..., description="镜头编号")
    duration: str = Field(..., description="时长，如 0:00-0:05")
    visual_description: str = Field(..., description="画面描述")
    dialogue: str = Field(..., description="台词")
    scene_suggestion: Optional[str] = Field(None, description="拍摄场景建议")
    camera_movement: Optional[str] = Field(None, description="运镜建议")
    notes: Optional[str] = Field(None, description="备注")


class ShootScriptRequest(BaseModel):
    """拍摄脚本生成请求"""
    topic: str = Field(..., min_length=1, max_length=500, description="话题/主题")
    platform: PlatformType = Field(..., description="目标平台")
    style: ScriptStyle = Field(default=ScriptStyle.ENERGETIC, description="脚本风格")
    persona: Optional[str] = Field(None, max_length=200, description="人设")
    # 目标时长（秒）：60 / 120 / 180 / 300（B站长视频默认）。前端可选。
    duration_seconds: Optional[int] = Field(
        None, ge=15, le=900, description="目标时长（秒），未指定时按平台默认"
    )

    # 热点关联（用于内容库追踪）
    hot_topic_id: Optional[str] = Field(None, description="关联的热点ID")
    hot_topic_title: Optional[str] = Field(None, description="关联的热点标题")
    hot_topic_source: Optional[str] = Field(None, description="关联的热点来源")


class ShootScriptResponse(BaseModel):
    """拍摄脚本响应"""
    id: str
    topic: str
    platform: PlatformType
    style: ScriptStyle
    persona: Optional[str]
    shots: List[Shot]
    title: str
    hooks: List[str]
    call_to_action: str
    tags: List[str]
    estimated_duration: str
    created_at: datetime

    class Config:
        from_attributes = True


class ScriptExportRequest(BaseModel):
    """脚本导出请求"""
    script_id: str
    format: str = Field(..., pattern="^(json|txt|csv)$", description="导出格式")
