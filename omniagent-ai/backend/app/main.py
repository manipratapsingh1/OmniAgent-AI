from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import (
    auth, chat, conversations, document, tasks, tools, admin, health,
    api_keys, notifications, memory, background_jobs, feedback, quota, search, features,
    advanced_tools, debug
)
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestContextMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.init_db import init_db
from app.logging_conf import configure_logging, log
from app.metrics import prometheus_middleware, router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    settings = get_settings()
    configure_logging(settings.APP_DEBUG)
    
    # Initialize database and seed if needed
    log.info("app.startup", app=settings.APP_NAME, version="2.0.0")
    try:
        init_db()
        log.info("app.startup.database_ready")
    except Exception as e:
        from app.utils.db_diagnostics import diagnose_database_connection
        diagnostics = diagnose_database_connection()
        
        log.critical(
            "app.startup.database_failed",
            error=str(e),
            error_type=type(e).__name__,
            diagnostics=diagnostics,
        )
        
        # Print helpful error message to console
        print("\n" + "="*60)
        print("DATABASE CONNECTION FAILED")
        print("="*60)
        if diagnostics.get("error"):
            print(diagnostics["error"])
        print("\nFull error:")
        print(str(e))
        print("="*60 + "\n")
        
        raise
    
    yield
    
    # Cleanup on shutdown
    log.info("app.shutdown")


def create_app() -> FastAPI:
    """Create and configure FastAPI application with production optimizations"""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version="2.0.0",
        description="Production-ready AI Agent Platform with RAG, Memory, and Task Automation",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Parse CORS origins from comma-separated string
    cors_origins = [
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
    ] if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS

    # 1. Trusted Host Middleware (security)
    app.add_middleware(
        TrustedHostMiddleware,
        # include 'testserver' to allow requests from FastAPI TestClient in tests
        allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.example.com"],
    )

    # 2. Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. GZIP Compression Middleware (performance)
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,  # Only compress responses > 1KB
    )

    # 4. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 5. Custom Request Context Middleware
    app.add_middleware(RequestContextMiddleware)

    # 6. Prometheus metrics middleware (non-blocking)
    try:
        app.middleware('http')(prometheus_middleware(app))
        app.include_router(metrics_router, prefix="", tags=["metrics"])
    except Exception:
        log.warning("app.metrics.disabled", reason="prometheus not available or failed to initialize")

    # Register exception handlers
    register_exception_handlers(app)

    # Include all routers with prefixes
    app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
    app.include_router(document.router, prefix="/api/v1/documents", tags=["documents"])
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
    app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
    app.include_router(advanced_tools.router, prefix="/api/v1/tools", tags=["advanced-tools"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(api_keys.router, prefix="/api/v1", tags=["api-keys"])
    app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
    app.include_router(memory.router, prefix="/api/v1", tags=["memory"])
    app.include_router(background_jobs.router, prefix="/api/v1", tags=["background-jobs"])
    app.include_router(debug.router, prefix="/api/v1", tags=["debug"])
    app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
    app.include_router(quota.router, prefix="/api/v1", tags=["quota"])
    app.include_router(search.router, prefix="/api/v1", tags=["search"])
    app.include_router(features.router, prefix="/api/v1", tags=["features"])
    # Assistant router (feature-flagged)
    try:
        from app.api.v1 import assistant
        if settings.ASSISTANT_ENABLED:
            app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["assistant"])
    except Exception:
        log.warning("assistant.router.disabled", reason="failed to register assistant router")

    log.info("app.initialized", routes_count=len(app.routes))
    # Add a root-level health endpoint for simple liveness checks (/healthz)
    @app.get("/healthz")
    async def _root_health():
        return await health.healthz()
    return app


# Create the FastAPI application instance
app = create_app()