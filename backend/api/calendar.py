"""
日历 API 路由
提供日历事件的 CRUD 接口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.services.calendar_service import calendar_service
from backend.models.domain.calendar import CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse
from backend.models.database.tables import UserTable
from backend.api.dependencies import get_current_user

# 创建路由
router = APIRouter(prefix="/calendar", tags=["日历"])


class EventListResponse(BaseModel):
    """事件列表响应"""
    events: list[CalendarEventResponse]
    total: int


class MessageResponse(BaseModel):
    """消息响应"""
    message: str
    event_id: int | None = None


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: CalendarEventCreate,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建日历事件

    - title: 事件标题（1-200字符）
    - content: 事件内容（可选）
    - scheduled_date: 计划发布日期
    - platform: 发布平台（可选）
    - status: 事件状态（可选，默认 pending）

    需要认证，不消耗配额
    """
    try:
        event = calendar_service.create_event(db, current_user.id, event_data)
        return event

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "server_error", "message": f"创建事件失败: {str(e)}"}
        )


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_event(
    event_id: int,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个日历事件

    需要认证
    """
    event = calendar_service.get_event(db, current_user.id, event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "事件不存在"}
        )

    return event


@router.get("/events", response_model=EventListResponse)
async def get_events(
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: str = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(None, description="结束日期 (YYYY-MM-DD)"),
    status_filter: str = Query(None, alias="status", description="状态筛选")
):
    """
    获取用户的日历事件列表

    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）
    - status: 状态筛选（可选）

    需要认证，返回按计划日期排序的事件列表
    """
    try:
        # 解析日期字符串
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        events = calendar_service.get_events(
            db,
            current_user.id,
            start_date=start_dt,
            end_date=end_dt,
            status=status_filter
        )

        return EventListResponse(
            events=events,
            total=len(events)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_date", "message": f"日期格式错误: {str(e)}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "server_error", "message": f"获取事件列表失败: {str(e)}"}
        )


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: int,
    event_data: CalendarEventUpdate,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新日历事件

    - title: 事件标题（可选）
    - content: 事件内容（可选）
    - scheduled_date: 计划发布日期（可选）
    - platform: 发布平台（可选）
    - status: 事件状态（可选）

    需要认证
    """
    try:
        event = calendar_service.update_event(db, current_user.id, event_id, event_data)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "事件不存在"}
            )

        return event

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "server_error", "message": f"更新事件失败: {str(e)}"}
        )


@router.delete("/events/{event_id}", response_model=MessageResponse)
async def delete_event(
    event_id: int,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除日历事件

    需要认证
    """
    success = calendar_service.delete_event(db, current_user.id, event_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "事件不存在"}
        )

    return MessageResponse(message="事件已删除", event_id=event_id)


@router.get("/events/upcoming", response_model=EventListResponse)
async def get_upcoming_events(
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=90, description="未来天数")
):
    """
    获取未来指定天数内的日历事件

    - days: 未来天数（默认7天，最大90天）

    需要认证
    """
    try:
        events = calendar_service.get_upcoming_events(db, current_user.id, days)

        return EventListResponse(
            events=events,
            total=len(events)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "server_error", "message": f"获取即将到来事件失败: {str(e)}"}
        )
