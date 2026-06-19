from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from app.deps import db_session, current_user
from app.models.user import User
from app.services.background_job_service import BackgroundJobService

router = APIRouter()


class BackgroundJobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    progress: int
    result: Optional[str]
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)


@router.get("/jobs", response_model=List[BackgroundJobResponse])
def get_user_jobs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Get user's background jobs"""
    service = BackgroundJobService(db)
    jobs = service.get_user_jobs(user.id, limit)
    
    return [
        BackgroundJobResponse(
            id=j.id,
            job_type=j.job_type,
            status=j.status,
            progress=j.progress,
            result=j.result,
            error=j.error,
            created_at=j.created_at.isoformat(),
            started_at=j.started_at.isoformat() if j.started_at else None,
            completed_at=j.completed_at.isoformat() if j.completed_at else None
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=BackgroundJobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Get specific job"""
    service = BackgroundJobService(db)
    job = service.get_job(job_id)
    
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return BackgroundJobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        result=job.result,
        error=job.error,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )


@router.delete("/jobs/{job_id}")
def cancel_job(
    job_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Cancel a background job"""
    service = BackgroundJobService(db)
    job = service.get_job(job_id)
    
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    success = service.cancel_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    return {"status": "cancelled"}
