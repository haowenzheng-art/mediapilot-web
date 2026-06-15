"""
内容库路由
使用统一的 API 响应模型
"""
import sys
import os
import logging
from typing import Optional

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.domain.content_library import (
    ContentCreate, ContentUpdate, ContentResponse,
    TopicHistoryRequest, TopicHistoryResponse, ContentType
)
from backend.models.schemas.api_response import ErrorCode
from backend.utils.api_response import (
    success_response,
    error_response
)
from backend.services.content_library_service import content_library_service
from backend.models.database.tables import UserTable

router = APIRouter(prefix="/content-library", tags=["内容库"])


def get_dev_user(db: Session) -> UserTable:
    """开发模式下获取默认用户"""
    user = db.query(UserTable).filter(UserTable.username == "dev").first()
    if not user:
        user = UserTable(
            username="dev",
            email="dev@mediapilot.local",
            password_hash="dev",
            quota_balance=9999,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/contents")
async def get_contents(
    content_type: Optional[str] = Query(None, description="内容类型: copywriting, shoot_script"),
    is_processed: Optional[bool] = Query(None, description="是否已处理"),
    hot_topic_id: Optional[str] = Query(None, description="热点ID"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取用户的内容列表

    支持筛选：
    - content_type: 内容类型
    - is_processed: 是否已处理
    - hot_topic_id: 关联的热点ID
    """
    user = get_dev_user(db)

    try:
        # 验证 content_type
        content_type_enum = None
        if content_type:
            try:
                content_type_enum = ContentType(content_type)
            except ValueError:
                return error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message=f"无效的内容类型: {content_type}",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        contents = content_library_service.get_user_contents(
            db=db,
            user_id=user.id,
            content_type=content_type_enum,
            is_processed=is_processed,
            hot_topic_id=hot_topic_id,
            limit=limit,
            offset=offset
        )

        return success_response(
            data={"contents": contents, "count": len(contents)},
            message="获取内容列表成功"
        )
    except Exception as e:
        logger.error(f"获取内容列表失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取内容列表失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/contents")
async def create_content(
    content_in: ContentCreate,
    db: Session = Depends(get_db)
):
    """
    创建内容记录

    用于在生成文案/脚本后自动保存到内容库
    """
    user = get_dev_user(db)

    try:
        content = content_library_service.create_content(db, user.id, content_in)
        return success_response(
            data={"content": content},
            message="创建内容成功"
        )
    except Exception as e:
        logger.error(f"创建内容失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"创建内容失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/contents/{content_id}")
async def get_content(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单条内容详情
    """
    user = get_dev_user(db)

    try:
        content = content_library_service.get_content_by_id(db, content_id)

        if not content:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="内容不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if content.user_id != user.id:
            return error_response(
                code=ErrorCode.FORBIDDEN,
                message="无权访问此内容",
                status_code=status.HTTP_403_FORBIDDEN
            )

        return success_response(
            data={"content": content},
            message="获取内容成功"
        )
    except Exception as e:
        logger.error(f"获取内容失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取内容失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/contents/{content_id}")
async def update_content(
    content_id: int,
    content_in: ContentUpdate,
    db: Session = Depends(get_db)
):
    """
    更新内容记录
    """
    user = get_dev_user(db)

    try:
        content = content_library_service.update_content(db, content_id, user.id, content_in)
        return success_response(
            data={"content": content},
            message="更新内容成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"更新内容失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"更新内容失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/contents/{content_id}")
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    删除内容记录
    """
    user = get_dev_user(db)

    try:
        success = content_library_service.delete_content(db, content_id, user.id)
        if success:
            return success_response(
                data={"content_id": content_id},
                message="删除内容成功"
            )
        else:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="内容不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"删除内容失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"删除内容失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/contents/{content_id}/process")
async def mark_as_processed(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    标记内容为已处理

    用户将内容用于创作后，标记为已处理
    """
    user = get_dev_user(db)

    try:
        content = content_library_service.mark_as_processed(db, content_id, user.id)
        return success_response(
            data={"content": content},
            message="标记已处理成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"标记已处理失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"标记已处理失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/hot-topic/{hot_topic_id}/contents")
async def get_hot_topic_contents(
    hot_topic_id: str,
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取热点关联的内容

    查看基于该热点生成的所有文案和脚本
    """
    user = get_dev_user(db)

    try:
        contents = content_library_service.get_hot_topic_contents(
            db=db,
            hot_topic_id=hot_topic_id,
            user_id=user.id,
            limit=limit
        )

        return success_response(
            data={"contents": contents, "count": len(contents)},
            message="获取热点关联内容成功"
        )
    except Exception as e:
        logger.error(f"获取热点关联内容失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取热点关联内容失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/topic-history")
async def get_topic_history(
    request: TopicHistoryRequest,
    db: Session = Depends(get_db)
):
    """
    获取话题的历史趋势

    查看热点话题的热度变化趋势
    """
    try:
        history = content_library_service.get_topic_history(
            db=db,
            hot_topic_id=request.hot_topic_id,
            limit=request.limit
        )

        return success_response(
            data=history.model_dump(),
            message="获取话题历史趋势成功"
        )
    except Exception as e:
        logger.error(f"获取话题历史趋势失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取话题历史趋势失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return success_response(data={"status": "ok"}, message="内容库服务正常")