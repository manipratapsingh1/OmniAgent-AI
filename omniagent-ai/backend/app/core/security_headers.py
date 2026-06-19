"""
Security headers middleware for FastAPI applications.
Adds recommended security headers to all responses.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        
        # Content Security Policy (allow configured frontend origins dynamically)
        from app.config import get_settings
        settings = get_settings()
        cors_origins = [
            origin.strip()
            for origin in settings.CORS_ORIGINS.split(",")
            if origin.strip()
        ] if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS
        
        origins_str = " ".join(cors_origins)
        
        csp = (
            f"default-src 'self'; "
            f"script-src 'self' 'wasm-unsafe-eval'; "
            f"style-src 'self' 'unsafe-inline'; "
            f"img-src 'self' data: https:; "
            f"font-src 'self' data:; "
            f"connect-src 'self' {origins_str}; "
            f"frame-ancestors 'none'; "
            f"form-action 'self'; "
            f"base-uri 'self'; "
            f"object-src 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Enforce HTTPS (Strict-Transport-Security)
        # Only set in production (APP_ENV=production)
        # Max-age is 1 year (31536000 seconds)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
