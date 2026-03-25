"""
自定义异常定义
"""


class MediaPilotException(Exception):
    """MediaPilot 基础异常"""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(MediaPilotException):
    """验证错误"""

    def __init__(self, message: str):
        super().__init__(message, code=400)


class APIError(MediaPilotException):
    """API 调用错误"""

    def __init__(self, message: str, provider: str = None):
        self.provider = provider
        super().__init__(message, code=502)


class TaskNotFoundError(MediaPilotException):
    """任务未找到错误"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"任务 {task_id} 不存在", code=404)


class DatabaseError(MediaPilotException):
    """数据库错误"""

    def __init__(self, message: str):
        super().__init__(message, code=500)


class ExternalServiceError(MediaPilotException):
    """外部服务错误"""

    def __init__(self, message: str, service: str = None):
        self.service = service
        super().__init__(message, code=503)
