from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import structlog

log = structlog.get_logger("validation")


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, detail: str, field: str = None, status_code: int = 422):
        self.detail = detail
        self.field = field
        self.status_code = status_code


class RateLimitExceeded(Exception):
    """Rate limit exceeded error"""
    def __init__(self, detail: str = "Rate limit exceeded", retry_after: int = 60):
        self.detail = detail
        self.retry_after = retry_after


class InsufficientQuota(Exception):
    """Insufficient API quota error"""
    def __init__(self, detail: str = "API quota exceeded"):
        self.detail = detail


def register_exception_handlers(app):
    """Register custom exception handlers"""
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        log.warning(
            "validation.error",
            detail=exc.detail,
            field=exc.field,
            path=request.url.path
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "validation_error",
                "message": exc.detail,
                "field": exc.field,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        log.warning("rate_limit.exceeded", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": exc.detail,
                "retry_after": exc.retry_after,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Retry-After": str(exc.retry_after)}
        )
    
    @app.exception_handler(InsufficientQuota)
    async def quota_handler(request: Request, exc: InsufficientQuota):
        log.warning("quota.exceeded", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={
                "error": "insufficient_quota",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
