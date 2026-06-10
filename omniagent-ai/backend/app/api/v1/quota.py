from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel

from app.deps import db_session, current_user
from app.models.user import User
from app.services.quota_service import QuotaService

router = APIRouter()


class QuotaResponse(BaseModel):
    quota: int
    used: int
    remaining: int
    usage_percentage: float
    status: str


@router.get("/quota", response_model=QuotaResponse)
def get_user_quota(
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Get current API quota usage"""
    service = QuotaService(db)
    stats = service.get_user_stats(user.id)
    
    return QuotaResponse(
        quota=stats["quota"],
        used=stats["used"],
        remaining=stats["remaining"],
        usage_percentage=stats["usage_percentage"],
        status=stats["status"]
    )
