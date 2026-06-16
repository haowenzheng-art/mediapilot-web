"""
导入 API 路由
提供数据导入接口（支持 CSV/Excel）
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any

from backend.config.database import get_db
from backend.services.import_export_service import import_export_service
from backend.api.dependencies import get_current_user
from backend.models.database.tables import UserTable

router = APIRouter(prefix="/import", tags=["数据导入"])


@router.post("/trending")
async def import_trending(
    file: UploadFile = File(..., description="CSV 文件"),
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    导入热点话题

    不消耗配额
    """
    try:
        content = await file.read()

        # 解析 CSV
        if file.filename.endswith('.csv'):
            import io
            import csv
            reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
            topics = []
            for row in reader:
                topics.append({
                    "keyword": row.get("关键词", ""),
                    "platform": row.get("平台", ""),
                    "heat_value": int(row.get("热度值", "0")),
                    "trend": row.get("趋势", "")
                })

            # 批量保存到数据库
            imported = await import_export_service.import_hot_topics(db, topics, current_user.id)

            return {
                "success": True,
                "message": f"成功导入 {imported} 条热点话题",
                "imported": imported
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_format", "message": "仅支持 CSV 格式"}
            )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "parse_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "server_error", "message": f"导入失败: {str(e)}"}
        )


@router.post("/competitors")
async def import_competitors(
    file: UploadFile = File(..., description="CSV 文件"),
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    导入对标账号

    不消耗配额
    """
    try:
        content = await file.read()

        if file.filename.endswith('.csv'):
            import io
            import csv
            reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
            competitors = []
            for row in reader:
                competitors.append({
                    "username": row.get("用户名", ""),
                    "platform": row.get("平台", ""),
                    "niche": row.get("赛道", ""),
                    "followers": int(row.get("粉丝数", "0")),
                    "likes": int(row.get("点赞数", "0")),
                    "posts_count": int(row.get("作品数", "0"))
                })

            imported = await import_export_service.import_competitors(db, competitors, current_user.id)

            return {
                "success": True,
                "message": f"成功导入 {imported} 个对标账号",
                "imported": imported
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_format", "message": "仅支持 CSV 格式"}
            )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "parse_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "server_error", "message": f"导入失败: {str(e)}"}
        )


@router.post("/calendar")
async def import_calendar(
    file: UploadFile = File(..., description="CSV 文件"),
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    导入日历事件

    不消耗配额
    """
    try:
        content = await file.read()

        if file.filename.endswith('.csv'):
            import io
            import csv
            from datetime import datetime
            reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
            events = []
            for row in reader:
                events.append({
                    "title": row.get("标题", ""),
                    "content": row.get("内容", ""),
                    "scheduled_date": datetime.fromisoformat(row.get("计划日期", "")),
                    "platform": row.get("平台", ""),
                    "status": row.get("状态", "pending")
                })

            imported = await import_export_service.import_calendar_events(db, events, current_user.id)

            return {
                "success": True,
                "message": f"成功导入 {imported} 个日历事件",
                "imported": imported
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_format", "message": "仅支持 CSV 格式"}
            )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "parse_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "server_error", "message": f"导入失败: {str(e)}"}
        )
