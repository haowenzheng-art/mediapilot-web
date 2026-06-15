"""
日历 API 路由
提供日历事件的 CRUD 接口
使用统一响应格式和分页
"""
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.services.calendar_service import calendar_service
from backend.models.domain.calendar import CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse
from backend.models.database.tables import UserTable
from backend.api.dependencies import get_current_user
from backend.utils.api_response import success_response, error_response, paginated_response
from backend.models.schemas.api_response import ErrorCode

router = APIRouter(prefix="/calendar", tags=["日历"])


@router.post("/events", status_code=status.HTTP_201_CREATED)
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
        return success_response(
            data=event,
            message="创建事件成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"创建事件失败: {str(e)}"
        )


@router.get("/events/{event_id}")
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
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="事件不存在",
            status_code=status.HTTP_404_NOT_FOUND
        )

    return success_response(
        data=event,
        message="获取事件成功"
    )


@router.get("/events")
async def get_events(
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    page: Optional[int] = Query(1, ge=1, description="页码"),
    per_page: Optional[int] = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取用户的日历事件列表（支持分页）

    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）
    - status: 状态筛选（可选）
    - page: 页码（默认值：1）
    - per_page: 每页数量（默认值：20）

    需要认证，返回按计划日期排序的事件列表
    """
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        validated_page = max(page or 1, 1)
        validated_per_page = min(max(per_page or 20, 1), 100)

        events, total = calendar_service.get_events(
            db,
            current_user.id,
            start_date=start_dt,
            end_date=end_dt,
            status=status_filter,
            page=validated_page,
            per_page=validated_per_page
        )

        return paginated_response(
            data=events,
            total=total,
            page=validated_page,
            per_page=validated_per_page
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=f"日期格式错误: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取事件列表失败: {str(e)}"
        )


@router.put("/events/{event_id}")
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
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="事件不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return success_response(
            data=event,
            message="更新事件成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"更新事件失败: {str(e)}"
        )


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除日历事件

    需要认证
    """
    try:
        success = calendar_service.delete_event(db, current_user.id, event_id)

        if not success:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="事件不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return success_response(
            data={"event_id": event_id},
            message="删除事件成功"
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"删除事件失败: {str(e)}"
        )


@router.get("/events/upcoming")
async def get_upcoming_events(
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: Optional[int] = Query(7, ge=1, le=90, description="未来天数")
):
    """
    获取未来指定天数内的日历事件

    - days: 未来天数（默认7天，最大90天）

    需要认证
    """
    try:
        events = calendar_service.get_upcoming_events(db, current_user.id, days)

        return success_response(
            data=events,
            message=f"获取即将到来事件成功"
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取即将到来事件失败: {str(e)}"
        )
