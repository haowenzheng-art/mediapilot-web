"""
系统配置路由
"""
from fastapi import APIRouter
from backend.models.schemas.response import APIResponse
from backend.services.auth_service import AuthService

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
