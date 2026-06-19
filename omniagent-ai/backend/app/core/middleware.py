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
        rate_limit_key = client_ip
        
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                from app.core.security import decode_token
                payload = decode_token(token)
                if payload and "sub" in payload:
                    rate_limit_key = f"user:{payload['sub']}"
            except Exception:
                pass

        try:
            await enforce_rate_limit(rate_limit_key)
        except Exception as e:
            from fastapi.responses import JSONResponse
            # Handle rate limit exceeded cleanly
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please try again later."})

        import asyncio
        start = time.perf_counter()
        
        # Determine gateway timeout: 180s for streams, 30s otherwise
        is_stream = "stream" in request.url.path
        timeout_seconds = 180.0 if is_stream else 30.0

        try:
            response = await asyncio.wait_for(call_next(request), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            from fastapi.responses import JSONResponse
            logger.error("http.timeout", path=request.url.path, timeout=timeout_seconds)
            return JSONResponse(
                status_code=504,
                content={"detail": "Request gateway timeout"}
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["x-request-id"] = request_id
        logger.info(
            "http.request",
            method=request.method,
            status=response.status_code,
            elapsed_ms=round(elapsed_ms, 2),
        )
        return response