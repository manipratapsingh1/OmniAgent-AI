from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
import structlog

from app.deps import db_session, current_user
from app.models.user import User
from app.models.background_job import BackgroundJob
from app.models.memory import MemoryEntry
from app.services.memory_service import MemoryService
from app.services.background_job_service import BackgroundJobService
from app.utils.performance import get_perf_monitor, get_response_cache

log = structlog.get_logger("debug")
router = APIRouter()


@router.get("/debug/status")
def get_debug_status(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Debug dashboard payload with performance, cache, memory and job stats."""
    perf_monitor = get_perf_monitor()
    cache_stats = get_response_cache().stats()
    job_service = BackgroundJobService(db)
    jobs = db.exec(select(BackgroundJob)).all()

    job_status_counts = {
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
        "cancelled": 0,
    }
    for job in jobs:
        status = (job.status or "unknown").lower()
        if status not in job_status_counts:
            job_status_counts[status] = 0
        job_status_counts[status] += 1

    memory_service = MemoryService(db)
    user_counts = memory_service.get_counts(user.id)
    global_counts = memory_service.get_counts(None)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "perf_metrics": perf_monitor.get_all_stats(),
        "cache": cache_stats,
        "jobs": {
            "total": len(jobs),
            **job_status_counts,
        },
        "memory": {
            "per_user": user_counts,
            "global": global_counts,
        },
        "current_user": {"id": user.id, "email": user.email},
    }
