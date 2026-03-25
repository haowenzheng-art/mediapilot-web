"""
系统配置路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter
from models.schemas.response import APIResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/ai", tags=["系统配置"])

# 初始化服务
auth_service = AuthService()


@router.post("/configure", response_model=APIResponse)
async def configure_ai(provider: str, api_key: str, base_url: str = None, model: str = None):
    """配置AI服务"""
    result = await auth_service.configure_ai(provider, api_key, base_url, model)
    return APIResponse(
        success=result["success"],
        message=result["message"]
    )
