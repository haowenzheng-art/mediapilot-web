"""
MediaPilot API 速率限制中间件

实现要点：
- 滑动窗口 + 自动 GC 过期记录，避免内存无限增长
- 限流键 = 端点 + IP（认证用户可叠加 user_id 维度）
- 默认 60 次/分钟兜底
"""
import time
import logging
import threading
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# 端点级速率限制配置
RATE_LIMITS = {
    "api_v1_trending_search": {"calls": 30, "period": 60},
    "api_v1_trending_export": {"calls": 10, "period": 3600},
    "api_v1_competitors_search": {"calls": 20, "period": 3600},
    "api_v1_content_generate": {"calls": 5, "period": 60},
    "api_v1_video_transcribe": {"calls": 10, "period": 60},
    "api_v1_agent_run": {"calls": 10, "period": 60},
}

DEFAULT_LIMIT = {"calls": 60, "period": 60}

# 健康检查等路径跳过限流
EXEMPT_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


class RateLimiter:
    """线程安全的滑动窗口速率限制器"""

    def __init__(self):
        self._lock = threading.Lock()
        self._requests: dict[str, deque] = defaultdict(deque)
        self._last_gc = time.time()

    def is_allowed(self, key: str, limit_calls: int, period: int) -> bool:
        now = time.time()
        with self._lock:
            # 每 60s 触发一次全局 GC，回收空 deque
            if now - self._last_gc > 60:
                self._gc(now, period)
                self._last_gc = now

            bucket = self._requests[key]
            cutoff = now - period
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit_calls:
                return False
            bucket.append(now)
            return True

    def _gc(self, now: float, max_period: int) -> None:
        """清理所有过期桶，回收空 deque"""
        cutoff = now - max_period
        empty_keys = []
        for k, bucket in self._requests.items():
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if not bucket:
                empty_keys.append(k)
        for k in empty_keys:
            self._requests.pop(k, None)


_global_limiter = RateLimiter()


def _get_rate_limit_for_endpoint(endpoint_name: str) -> dict:
    return RATE_LIMITS.get(endpoint_name, DEFAULT_LIMIT)


def _resolve_user_id(request: Request) -> str | None:
    """尽量从已认证的 request.state 中提取 user_id"""
    user = getattr(request.state, "user", None)
    if user is not None:
        uid = getattr(user, "id", None) or getattr(user, "sub", None)
        if uid is not None:
            return str(uid)
    return None


def create_rate_limiting_middleware():
    """创建速率限制中间件"""
    async def middleware(request: Request, call_next):
        path = request.url.path
        if path in EXEMPT_PATHS:
            return await call_next(request)

        endpoint_name = f"api{path.replace('/', '_')}"
        limit_config = _get_rate_limit_for_endpoint(endpoint_name)

        ip = request.client.host if request.client else "unknown"
        user_id = _resolve_user_id(request)
        identity = f"u{user_id}" if user_id else f"ip_{ip}"
        full_key = f"{endpoint_name}:{identity}"

        if not _global_limiter.is_allowed(
            full_key, limit_config["calls"], limit_config["period"]
        ):
            logger.warning(
                f"Rate limit exceeded: {request.method} {path} identity={identity}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "请求过于频繁，请稍后再试",
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "超过速率限制",
                        "retry_after": limit_config["period"],
                    },
                },
                headers={"Retry-After": str(limit_config["period"])},
            )

        return await call_next(request)

    return middleware
