"""
MediaPilot 领域模型
定义核心业务实体
"""
from .hot_topic import HotTopic
from .competitor import CompetitorAccount
from .content import Shot, Copywriting
from .task import Task, TaskStatus
from .user import User, UserCreate, UserLogin, UserResponse, QuasiRecharge, QuasiResponse
from .calendar import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse
)
from .content_library import (
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    TopicHistoryRequest,
    TrendRecordResponse,
    TopicHistoryResponse,
    TrendDirection,
    ContentType
)

__all__ = [
    'HotTopic',
    'CompetitorAccount',
    'Shot',
    'Copywriting',
    'Task',
    'TaskStatus',
    'User',
    'UserCreate',
    'UserLogin',
    'UserResponse',
    'QuasiRecharge',
    'QuasiResponse',
    'CalendarEventCreate',
    'CalendarEventUpdate',
    'CalendarEventResponse',
    'ContentCreate',
    'ContentUpdate',
    'ContentResponse',
    'TopicHistoryRequest',
    'TrendRecordResponse',
    'TopicHistoryResponse',
    'TrendDirection',
    'ContentType',
]
