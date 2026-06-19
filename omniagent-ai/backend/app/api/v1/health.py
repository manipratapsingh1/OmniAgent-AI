from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import httpx
import redis.asyncio as redis
import structlog
from sqlmodel import Session, text
import asyncio

from app.config import get_settings
from app.db.session import get_session
from app.utils.health_check import HealthChecker, get_performance_monitor

log = structlog.get_logger("health")

router = APIRouter()
_settings = get_settings()


@router.get("/healthz")
async def healthz():
    """Basic liveness probe for Kubernetes"""
    return {
        "status": "alive",
        "service": "omniagent-api",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/readyz")
async def readyz():
    """Readiness probe - verify all critical services are operational"""
    checks = {
        "database": False,
        "redis": False,
        "ollama": False,
        "chroma": False,
    }

    # Test database connection in thread pool to avoid blocking
    try:
        loop = asyncio.get_event_loop()
        db_result = await asyncio.wait_for(
            loop.run_in_executor(None, test_database_sync),
            timeout=3.0
        )
        checks["database"] = db_result
        if db_result:
            log.debug("health.database.ok")
        else:
            log.error("health.database.failed")
    except asyncio.TimeoutError:
        checks["database"] = False
        log.error("health.database.timeout")
    except Exception as e:
        checks["database"] = False
        log.error("health.database.exception", error=str(e))

    # Test Redis connection with timeout
    try:
        redis_client = redis.from_url(_settings.REDIS_URL, socket_connect_timeout=2)
        await asyncio.wait_for(redis_client.ping(), timeout=2.0)
        await redis_client.aclose()
        checks["redis"] = True
        log.debug("health.redis.ok")
    except asyncio.TimeoutError:
        checks["redis"] = False
        log.error("health.redis.timeout")
    except Exception as e:
        checks["redis"] = False
        log.error("health.redis.failed", error=str(e))

    # Test Ollama connection with timeout
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await asyncio.wait_for(
                client.get(f"{_settings.OLLAMA_BASE_URL}/api/tags"),
                timeout=2.5
            )
            checks["ollama"] = response.status_code == 200
        if checks["ollama"]:
            log.debug("health.ollama.ok")
        else:
            log.error("health.ollama.failed", status=response.status_code)
    except asyncio.TimeoutError:
        checks["ollama"] = False
        log.error("health.ollama.timeout")
    except Exception as e:
        checks["ollama"] = False
        log.error("health.ollama.failed", error=str(e))

    # Test Chroma connection with timeout
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await asyncio.wait_for(
                client.get(f"http://{_settings.CHROMA_HOST}:{_settings.CHROMA_PORT}/api/v2/tenants/default_tenant"),
                timeout=2.5
            )
            checks["chroma"] = response.status_code == 200
        if checks["chroma"]:
            log.debug("health.chroma.ok")
        else:
            log.error("health.chroma.failed", status=response.status_code)
    except asyncio.TimeoutError:
        checks["chroma"] = False
        log.error("health.chroma.timeout")
    except Exception as e:
        checks["chroma"] = False
        log.error("health.chroma.failed", error=str(e))

    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def test_database_sync() -> bool:
    """Synchronous database test (run in executor)"""
    try:
        session = get_session()
        result = session.exec(text("SELECT 1")).first()
        session.close()
        return result is not None
    except Exception as e:
        log.error("test_database_sync.failed", error=str(e))
        return False


@router.get("/detailed")
async def detailed_health():
    """Detailed health report with comprehensive component status and metrics"""
    try:
        # Get database session synchronously
        loop = asyncio.get_event_loop()
        db_ready = await loop.run_in_executor(None, test_database_sync)
        
        # Return comprehensive health status
        return {
            "status": "healthy" if db_ready else "degraded",
            "database": {"connected": db_ready},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        log.exception("detailed_health.failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/metrics")
async def metrics():
    """Get performance metrics for all endpoints"""
    perf_monitor = get_performance_monitor()
    stats = perf_monitor.get_all_stats()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": stats,
        "total_endpoints": len(stats),
    }