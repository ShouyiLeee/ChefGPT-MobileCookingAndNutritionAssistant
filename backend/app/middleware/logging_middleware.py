"""Request/response logging middleware."""
import time
from uuid import uuid4

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with request_id, method, path, status, latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid4())[:8]
        start = time.perf_counter()

        # Attach request_id so downstream code can reference it
        request.state.request_id = request_id

        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        status = response.status_code

        log = logger.info if status < 400 else logger.warning if status < 500 else logger.error
        log(
            "{method} {path} → {status} ({latency}ms) [{rid}]",
            method=request.method,
            path=request.url.path,
            status=status,
            latency=latency_ms,
            rid=request_id,
        )

        response.headers["X-Request-ID"] = request_id
        return response
