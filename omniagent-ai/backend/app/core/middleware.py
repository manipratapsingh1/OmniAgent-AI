import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog

from app.core.rate_limit import enforce_rate_limit

logger = structlog.get_logger("http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)

        client_ip = request.client.host if request.client else "unknown"
        try:
            await enforce_rate_limit(client_ip)
        except Exception as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=429, content={"detail": str(e)})

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["x-request-id"] = request_id
        logger.info(
            "http.request",
            method=request.method,
            status=response.status_code,
            elapsed_ms=round(elapsed_ms, 2),
        )
        return response