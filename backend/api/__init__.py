"""
MediaPilot API 路由注册模块
统一注册所有路由
"""
import sys
import os
import logging
from typing import Any
from fastapi import FastAPI, Request, HTTPException, status

# 确保父目录在路径中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.core.ai_service import ai_manager
from backend.core.transcribe_engine import TranscribeEngineManager

# 导入统一错误处理
from backend.utils.api_response import error_response
from backend.utils.exceptions_typed import DatabaseError

# 导入速率限制
from middleware.rate_limiting import create_rate_limiting_middleware

logger = logging.getLogger(__name__)


def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    记录所有未捕获的异常并返回统一错误响应
    """
    logger.error(f"未捕获的异常: {type(exc).__name__} - {str(exc)}", exc_info=True)

    return error_response(
        code="internal_error",
        message="服务器内部错误，请稍后重试",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def database_exception_handler(request: Request, exc: DatabaseError):
    """
    数据库异常处理器
    记录数据库错误并返回统一错误响应
    """
    logger.error(f"数据库错误: {str(exc)}", exc_info=True)

    return error_response(
        code="database_error",
        message="数据库操作失败",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP 异常处理器
    记录日志并返回标准 JSON 错误响应，而非重新抛出
    """
    logger.warning(f"HTTP 异常: {exc.status_code} - {exc.detail}")

    from fastapi.responses import JSONResponse
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=detail)


def register_routes(app: FastAPI, transcribe_engine=None):
    """
    注册所有路由

    Args:
        app: FastAPI 应用实例
        transcribe_engine: 转写引擎实例（可选）
    """
    # 添加全局异常处理器
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # 导入各模块的路由
    try:
        from .trending import router as trending_router
        from .content import router as content_router
        from .video import router as video_router
        from .media import router as media_router, set_transcribe_engine
        from .system import router as system_router
        from .auth import router as auth_router
        from .copywriting import router as copywriting_router
        from .shoot_script import router as shoot_script_router
        from .subscription import router as subscription_router
        from .content_library import router as content_library_router
        # AI Chat 路由（无需认证）
        from .ai_chat import router as ai_chat_router

        # 设置转写引擎
        if transcribe_engine is not None:
            set_transcribe_engine(transcribe_engine)

        # 注册路由，统一使用 /api/v1 前缀
        app.include_router(trending_router, prefix="/api/v1")
        app.include_router(content_router, prefix="/api/v1")
        app.include_router(video_router, prefix="/api/v1")
        app.include_router(media_router, prefix="/api/v1")
        app.include_router(system_router, prefix="/api/v1")
        app.include_router(auth_router, prefix="/api/v1")
        app.include_router(copywriting_router, prefix="/api/v1")
        app.include_router(shoot_script_router, prefix="/api/v1")
        app.include_router(subscription_router, prefix="/api/v1")
        app.include_router(content_library_router, prefix="/api/v1")
        # AI Chat 路由由 main.py 处理

        # 添加速率限制中间件
        app.middleware("http")(create_rate_limiting_middleware())

        logger.info("所有路由注册完成")

    except ImportError as e:
        logger.error(f"路由注册失败: {e}")
        raise


__all__ = ['register_routes']
