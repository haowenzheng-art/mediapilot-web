"""
MediaPilot API 速率限制中间
"""
import sys
import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# 定义速率限制配置
RATE_LIMITS = {
    "api_v1_trending_search": {"calls": 30, "period": 60},  # 30次/每分钟
    "api_v1_trending_export": {"calls": 10, "period": 3600},  # 10次/每小时
    "api_v1_competitors_search": {"calls": 20, "period": 3600},
    "api_v1_content_generate": {"calls": 5, "period": 60},
    "api_v1_video_transcribe": {"calls": 10, "period": 60},
}


class RateLimiter:
    """简单的内存速率限制器实现"""

    def __init__(self):
        self._requests = {}  # {key: [(timestamp, count), ...]}

    def is_allowed(self, key: str, limit_calls: int, period: int) -> bool:
        """
        检查是否允许请求

        Args:
            key: 限制键
            limit_calls: 允许的调用次数
            period: 时间窗口（秒）

        Returns:
            bool: 是否允许
        """
        import time
        current_time = time.time()

        # 获取或创建该键的请求记录
        if key not in self._requests:
            self._requests[key] = []

        # 清理过期记录
        cutoff_time = current_time - period
        self._requests[key] = [t for t in self._requests[key] if t > cutoff_time]

        # 检查是否超过限制
        if len(self._requests[key]) >= limit_calls:
            return False

        # 添加当前请求
        self._requests[key].append(current_time)
        return True


# 全局限流器
_global_limiter = RateLimiter()


def _get_rate_limit_for_endpoint(endpoint_name: str) -> dict:
    """
    获取端点的速率限制配置

    Args:
        endpoint_name: 端点名称

    Returns:
        dict: 速率限制配置
    """
    return RATE_LIMITS.get(endpoint_name, {"calls": 60, "period": 60})


def create_rate_limiting_middleware():
    """
    创建速率限制中间件

    Returns:
        中间件函数
    """
    async def middleware(request: Request, call_next):
        """
        速率限制中间件

        Args:
            request: FastAPI 请求对象
            call_next: 下一个中间件

        Returns:
            Response: 响应对象
        """
        # 获取端点名称
        path = request.url.path

        # 检查是否跳过健康检查等特殊路由
        if path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # 获取速率限制配置
        endpoint_name = f"api{path.replace('/', '_')}"
        limit_config = _get_rate_limit_for_endpoint(endpoint_name)

        # 使用 IP 地址作为限流键
        key = f"ip_{request.client.host}"
        full_key = f"{endpoint_name}:{key}"

        # 检查是否超过限制
        if not _global_limiter.is_allowed(full_key, limit_config["calls"], limit_config["period"]):
            logger.warning(f"Rate limit exceeded for {endpoint_name}: {request.method} {request.url}")

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "请求过于频繁，请稍后再试",
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "超过速率限制",
                        "retry_after": limit_config["period"]
                    }
                }
            )

        # 继续处理请求
        return await call_next(request)

    return middleware
