from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel
from typing import Optional

from app.deps import db_session, current_user
from app.models.user import User
from app.services.feedback_service import ResponseFeedbackService

router = APIRouter()


class FeedbackRequest(BaseModel):
    response_id: int
    helpful: Optional[bool] = None
    rating: Optional[int] = None


@router.post("/feedback")
def submit_feedback(
    req: FeedbackRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Submit feedback on a response"""
    if req.rating is not None and (req.rating < 1 or req.rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    service = ResponseFeedbackService(db)
    success = service.add_feedback(
        req.response_id,
        user.id,
        helpful=req.helpful,
        rating=req.rating
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Response not found")
    
    return {"status": "feedback recorded"}


@router.get("/feedback/stats")
def get_feedback_stats(
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Get feedback statistics"""
    service = ResponseFeedbackService(db)
    return service.get_feedback_stats()
