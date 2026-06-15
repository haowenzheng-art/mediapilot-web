"""
异常定义
使用 Python 类型提示，遵循 PEP 8 标准
"""
import logging

logger = logging.getLogger(__name__)


class MediaPilotException(Exception):
    """
    MediaPilot 基础异常

    遵循 PEP 8 标准定义自定义异常
    """
    def __init__(self, message: str, code: int = 500, details: dict = None):
        """
        初始化异常

        Args:
            message: 错误消息
            code: 错误代码（默认 500）
            details: 额外的详细信息
        """
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        """返回异常的字符串表示"""
        if self.details:
            return f"[{self.code}] {self.message}: {self.details}"
        return f"[{self.code}] {self.message}"


class ValidationError(MediaPilotException):
    """
    验证错误（客户端输入错误）

    HTTP 状态码: 400
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code=400, details=details)

    def __str__(self) -> str:
        return f"[VALIDATION_ERROR] {self.message}"


class APIError(MediaPilotException):
    """
    API 调用错误（外部服务错误）

    HTTP 状态码: 502
    """
    def __init__(self, message: str, provider: str = None, details: dict = None):
        super().__init__(message, code=502, details={"provider": provider, **(details or {})})

    def __str__(self) -> str:
        provider_info = f"Provider: {self.provider}" if self.provider else ""
        return f"[API_ERROR] {self.message} {provider_info}"


class DatabaseError(MediaPilotException):
    """
    数据库错误

    HTTP 状态码: 500
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code=500, details=details)

    def __str__(self) -> str:
        return f"[DATABASE_ERROR] {self.message}"


class TaskNotFoundError(MediaPilotException):
    """
    任务未找到错误

    HTTP 状态码: 404
    """
    def __init__(self, task_id: str, details: dict = None):
        super().__init__(
            f"任务 {task_id} 不存在",
            code=404,
            details={"task_id": task_id, **(details or {})}
        )

    def __str__(self) -> str:
        return f"[TASK_NOT_FOUND] 任务 {self.task_id} 不存在"


class ExternalServiceError(MediaPilotException):
    """
    外部服务错误

    HTTP 状态码: 503
    """
    def __init__(self, message: str, service: str = None, details: dict = None):
        super().__init__(
            message,
            code=503,
            details={"service": service, **(details or {})}
        )

    def __str__(self) -> str:
        service_info = f"Service: {self.service}" if self.service else ""
        return f"[EXTERNAL_SERVICE_ERROR] {self.message} {service_info}"
