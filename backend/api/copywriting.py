"""
口播文案生成路由
使用统一的 API 响应模型
"""
import sys
import os
import logging

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.domain.persona import (
    PersonaCreate, PersonaResponse,
    CopywritingGenerateRequest, CopywritingRewriteRequest
)
from backend.models.schemas.api_response import ErrorCode
from backend.utils.api_response import (
    success_response,
    error_response
)
from backend.services.persona_service import persona_service
from backend.services.copywriting_service import copywriting_service
from backend.services.content_library_service import content_library_service
from backend.models.database.tables import UserTable
from backend.api.dependencies import get_current_user
from backend.services.auth_service_typed import auth_service
from backend.models.domain.content_library import ContentCreate, ContentType

router = APIRouter(prefix="/copywriting", tags=["口播文案"])


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


@router.get("/personas")
async def get_personas(
    db: Session = Depends(get_db)
):
    """
    获取用户的人设列表（最近3条）
    """
    user = get_dev_user(db)

    try:
        personas = persona_service.get_user_personas(db, user.id)
        return success_response(
            data={"personas": personas},
            message="获取人设列表成功"
        )
    except Exception as e:
        logger.error(f"获取人设列表失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取人设列表失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/personas")
async def create_persona(
    persona_in: PersonaCreate,
    db: Session = Depends(get_db)
):
    """
    创建人设
    """
    user = get_dev_user(db)

    try:
        persona = persona_service.create_persona(db, user.id, persona_in)

        # 更新人设使用时间
        persona_service.update_persona_last_used(db, user.id, persona_in.persona_description)

        return success_response(
            data={"persona": persona},
            message="创建人设成功"
        )
    except Exception as e:
        logger.error(f"创建人设失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"创建人设失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/personas/{persona_id}")
async def delete_persona(
    persona_id: int,
    db: Session = Depends(get_db)
):
    """
    删除人设
    """
    user = get_dev_user(db)

    try:
        success = persona_service.delete_persona(db, persona_id)
        if success:
            return success_response(
                data={"persona_id": persona_id},
                message="删除人设成功"
            )
        else:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="人设不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        logger.error(f"删除人设失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"删除人设失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/generate")
async def generate_copywriting(
    request: CopywritingGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    生成口播文案

    支持三种模式：
    - from_zero: 从0到1，需要topic参数
    - hotspot: 热点框架，需要hotspot_content参数
    - rewrite: 改写，需要original_text参数
    """
    user = get_dev_user(db)

    # 检查配额
    if not auth_service.check_quota(db, user.id, "generate_copywriting"):
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        # 记录人设使用
        persona_service.update_persona_last_used(db, user.id, request.persona)

        # 生成文案
        result = copywriting_service.generate(request)

        # 保存到内容库
        try:
            content_create = ContentCreate(
                content_type=ContentType.COPYWRITING,
                content_id=result.id,
                title=result.title,
                summary=result.content[:200] if len(result.content) > 200 else result.content,
                hot_topic_id=None,  # 文案生成暂不关联热点
                hot_topic_title=None,
                hot_topic_source=None,
                mode=result.mode,
                persona=request.persona,
                platform=None,
                style=None
            )
            content_library_service.create_content(db, user.id, content_create)
        except Exception as e:
            # 内容库保存失败不影响文案生成，只记录日志
            logger.warning(f"保存文案到内容库失败: {e}")

        # 扣减配额
        auth_service.deduct_quota(db, user.id, "generate_copywriting")

        return success_response(
            data=result,
            message="生成文案成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"生成文案失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"生成文案失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/rewrite")
async def rewrite_copywriting(
    request: CopywritingRewriteRequest,
    db: Session = Depends(get_db)
):
    """
    改写文案（再改改功能）

    支持三个方向：
    - more_colloquial: 更口语化
    - add_emotion: 加情绪
    - add_opinion: 加观点
    """
    user = get_dev_user(db)

    # 获取原文案
    original = copywriting_service.get_copywriting(request.copywriting_id)
    if not original:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="文案不存在",
            status_code=status.HTTP_404_NOT_FOUND
        )

    # 检查配额
    if not auth_service.check_quota(db, user.id, "rewrite_copywriting"):
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        # 改写文案
        result = copywriting_service.rewrite(
            request.copywriting_id,
            request.direction,
            original.persona
        )

        # 扣减配额
        auth_service.deduct_quota(db, user.id, "rewrite_copywriting")

        return success_response(
            data=result,
            message="改写文案成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"改写文案失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"改写文案失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return success_response(data={"status": "ok"}, message="口播文案服务正常")


@router.get("/reference")
async def get_reference_content(
    keyword: str,
    platforms: str = "weibo,baidu,zhihu"
):
    """
    获取AI文案参考内容

    Args:
        keyword: 搜索关键词
        platforms: 平台列表，逗号分隔（weibo,baidu,zhihu）

    Returns:
        {
            "keyword": str,
            "weibo": List[Dict],
            "baidu": List[Dict],
            "zhihu": List[Dict],
            "summary": str
        }
    """
    try:
        from backend.scrapers.content_reference_scraper import content_reference_scraper

        platform_list = [p.strip() for p in platforms.split(",")]
        scraper = ContentReferenceScraper()

        results = await scraper.get_reference_content(
            keyword=keyword,
            platforms=platform_list,
            max_results=5
        )

        await scraper.close()

        return success_response(
            data=results,
            message="获取参考内容成功"
        )

    except Exception as e:
        logger.error(f"获取参考内容失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取参考内容失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
