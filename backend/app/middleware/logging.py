"""请求日志中间件"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("yft.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        request_id = getattr(request.state, "request_id", "-")
        logger.info(
            "%s %s %s %.0fms",
            request_id,
            request.method,
            request.url.path,
            duration,
        )
        return response
