"""
MediaPilot API 路由模块
统一注册所有路由
"""
import sys
import os

# 简保父目录在路径中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI


def register_routes(app: FastAPI):
    """
    注册所有路由

    Args:
        app: FastAPI 应用实例
    """
    # 导入各模块的路由
    from .trending import router as trending_router
    from .competitors import router as competitors_router
    from .content import router as content_router
    from .video import router as video_router
    from .media import router as media_router
    from .system import router as system_router

    # 注册路由，统一使用 /api/v1 前缀
    app.include_router(trending_router, prefix="/api/v1")
    app.include_router(competitors_router, prefix="/api/v1")
    app.include_router(content_router, prefix="/api/v1")
    app.include_router(video_router, prefix="/api/v1")
    app.include_router(media_router, prefix="/api/v1")
    app.include_router(system_router, prefix="/api/v1")


# 兼容旧版本：提供 router 对象
try:
    from api.routes import router as old_router
    router = old_router
except:
    # 创建空路由作为后备
    from fastapi import APIRouter
    router = APIRouter()

__all__ = ['register_routes', 'router']
