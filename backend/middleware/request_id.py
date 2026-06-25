"""
请求级中间件：注入 request_id，记录访问日志。
"""
import time
import uuid
import logging
from fastapi import Request

access_logger = logging.getLogger("backend.access")


def create_request_id_middleware():
    """每个请求注入唯一 ID，便于日志关联"""

    async def middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        start = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.monotonic() - start) * 1000
            access_logger.error(
                f"req_id={request_id} method={request.method} path={request.url.path} "
                f"status=500 elapsed_ms={elapsed_ms:.1f}",
                exc_info=True,
            )
            raise

        elapsed_ms = (time.monotonic() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        access_logger.info(
            f"req_id={request_id} method={request.method} path={request.url.path} "
            f"status={response.status_code} elapsed_ms={elapsed_ms:.1f}"
        )
        return response

    return middleware
