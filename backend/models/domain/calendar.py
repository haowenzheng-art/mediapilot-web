"""
日历事件领域模型
使用 from_attributes 配置支持从 ORM 对象转换
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class CalendarEventCreate(BaseModel):
    """创建日历事件请求"""
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=200, description="事件标题")
    content: Optional[str] = Field(None, max_length=1000, description="事件内容")
    scheduled_date: datetime = Field(..., description="计划发布日期")
    platform: Optional[str] = Field(None, max_length=50, description="发布平台")
    status: str = Field("pending", max_length=20, description="事件状态")


class CalendarEventUpdate(BaseModel):
    """更新日历事件请求"""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="事件标题")
    content: Optional[str] = Field(None, max_length=1000, description="事件内容")
    scheduled_date: Optional[datetime] = Field(None, description="计划发布日期")
    platform: Optional[str] = Field(None, max_length=50, description="发布平台")
    status: Optional[str] = Field(None, max_length=20, description="事件状态")


class CalendarEventResponse(BaseModel):
    """日历事件响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    content: Optional[str]
    scheduled_date: datetime
    platform: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
