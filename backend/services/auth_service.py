"""
认证授权业务逻辑
"""
from backend.core.ai_service import ai_manager


class AuthService:
    """认证服务"""

    def __init__(self):
        pass

    async def configure_ai(
        self,
        provider: str,
        api_key: str,
        base_url: str = None,
        model: str = None
    ) -> dict:
        """
        配置 AI 服务

        Args:
            provider: 服务提供商 (anthropic, openai, ark)
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称

        Returns:
            操作结果
        """
        try:
            ai_manager.configure_service(provider, api_key, base_url, model)
            return {"success": True, "message": "AI服务配置成功"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def is_ai_available(self) -> bool:
        """
        检查 AI 服务是否可用

        Returns:
            AI 服务是否可用
        """
        service = ai_manager.get_current_service()
        return service is not None and service.is_available()
