import os
import psutil
import time
import structlog
from typing import Dict, Any
from datetime import datetime, timezone
from sqlmodel import Session, select, func
from app.models.user import User
from app.models.message import Message
from app.models.document import Document
from app.models.agent_run import AgentRun

log = structlog.get_logger("monitoring")

class MonitoringService:
    """God-level observability: Tracks system resources and app performance."""
    
    def __init__(self, db: Session):
        self.db = db

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get CPU, Memory, Disk, and Process metrics."""
        process = psutil.Process(os.getpid())
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "process_usage_mb": process.memory_info().rss / (1024 * 1024)
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "uptime_seconds": time.time() - psutil.boot_time()
        }

    def get_application_metrics(self) -> Dict[str, Any]:
        """Get high-level app statistics."""
        return {
            "users": {
                "total": self.db.exec(select(func.count(User.id))).one() or 0,
                "active_today": self.db.exec(
                    select(func.count(User.id))
                    .where(User.updated_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0))
                ).one() or 0
            },
            "chat": {
                "total_messages": self.db.exec(select(func.count(Message.id))).one() or 0,
                "avg_response_time_ms": self.db.exec(select(func.avg(AgentRun.latency_ms))).one() or 0
            },
            "storage": {
                "total_documents": self.db.exec(select(func.count(Document.id))).one() or 0,
                "indexed_success_rate": self._get_indexed_rate()
            }
        }

    def _get_indexed_rate(self) -> float:
        total = self.db.exec(select(func.count(Document.id))).one() or 0
        if total == 0: return 1.0
        indexed = self.db.exec(select(func.count(Document.id)).where(Document.status == "indexed")).one() or 0
        return indexed / total

    def get_full_report(self) -> Dict[str, Any]:
        """Combine all metrics for the dashboard."""
        return {
            "system": self.get_system_metrics(),
            "application": self.get_application_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
