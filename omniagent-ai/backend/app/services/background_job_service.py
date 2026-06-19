from sqlmodel import Session, select
from app.models.background_job import BackgroundJob
from datetime import datetime, timezone
import structlog
import uuid

log = structlog.get_logger("background_jobs")


class BackgroundJobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self,
        user_id: int,
        job_type: str,
        data: dict = None
    ) -> BackgroundJob:
        """Create a new background job"""
        job = BackgroundJob(
            user_id=user_id,
            job_type=job_type,
            status="pending"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        log.info("background_job.created", job_id=job.id, job_type=job_type, user_id=user_id)
        return job

    def update_status(
        self,
        job_id: int,
        status: str,
        progress: int = None,
        result: str = None,
        error: str = None
    ) -> BackgroundJob:
        """Update job status"""
        job = self.db.exec(select(BackgroundJob).where(BackgroundJob.id == job_id)).first()
        
        if not job:
            return None
        
        job.status = status
        if progress is not None:
            job.progress = progress
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        
        if status == "processing" and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        elif status in ["completed", "failed"]:
            job.completed_at = datetime.now(timezone.utc)
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        log.info("background_job.updated", job_id=job_id, status=status, progress=progress)
        return job

    def get_job(self, job_id: int) -> BackgroundJob:
        """Get job by ID"""
        return self.db.exec(
            select(BackgroundJob).where(BackgroundJob.id == job_id)
        ).first()

    def get_user_jobs(self, user_id: int, limit: int = 50):
        """Get user's background jobs"""
        jobs = self.db.exec(
            select(BackgroundJob)
            .where(BackgroundJob.user_id == user_id)
            .order_by(BackgroundJob.created_at.desc())
            .limit(limit)
        ).all()
        return jobs

    def get_pending_jobs(self, job_type: str = None):
        """Get pending jobs"""
        query = select(BackgroundJob).where(BackgroundJob.status == "pending")
        
        if job_type:
            query = query.where(BackgroundJob.job_type == job_type)
        
        jobs = self.db.exec(query).all()
        return jobs

    def cancel_job(self, job_id: int) -> bool:
        """Cancel a job"""
        job = self.db.exec(
            select(BackgroundJob).where(BackgroundJob.id == job_id)
        ).first()
        
        if not job or job.status not in ["pending", "processing"]:
            return False
        
        job.status = "cancelled"
        job.completed_at = datetime.now(timezone.utc)
        self.db.add(job)
        self.db.commit()
        
        log.info("background_job.cancelled", job_id=job_id)
        return True
