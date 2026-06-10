from sqlmodel import Session, select
from app.models.response import Response
from datetime import datetime
from typing import List
import structlog

log = structlog.get_logger("feedback")


class ResponseFeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def store_response(
        self,
        conversation_id: int,
        user_id: int,
        content: str,
        citations: List[str] = None,
        reasoning_trace: str = None
    ) -> Response:
        """Store a response for feedback tracking"""
        response = Response(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            citations=citations or [],
            reasoning_trace=reasoning_trace
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        
        log.info("response.stored", response_id=response.id, user_id=user_id)
        return response

    def add_feedback(
        self,
        response_id: int,
        user_id: int,
        helpful: bool = None,
        rating: int = None
    ) -> bool:
        """Add user feedback to a response"""
        response = self.db.exec(
            select(Response).where(
                Response.id == response_id,
                Response.user_id == user_id
            )
        ).first()
        
        if not response:
            return False
        
        if helpful is not None:
            response.helpful = helpful
        
        if rating is not None and 1 <= rating <= 5:
            response.rating = rating
        
        self.db.add(response)
        self.db.commit()
        
        log.info("feedback.added", response_id=response_id, helpful=helpful, rating=rating)
        return True

    def get_positive_responses(self, limit: int = 50) -> List[Response]:
        """Get positive feedback responses for learning"""
        responses = self.db.exec(
            select(Response)
            .where(Response.helpful == True)
            .order_by(Response.created_at.desc())
            .limit(limit)
        ).all()
        
        return responses

    def get_feedback_stats(self) -> dict:
        """Get feedback statistics"""
        total = self.db.exec(select(Response).where(Response.helpful.is_not(None))).all()
        positive = self.db.exec(select(Response).where(Response.helpful == True)).all()
        
        if not total:
            return {
                "total_feedback": 0,
                "positive": 0,
                "negative": 0,
                "satisfaction_rate": 0.0
            }
        
        negative = len(total) - len(positive)
        satisfaction_rate = len(positive) / len(total) if total else 0.0
        
        return {
            "total_feedback": len(total),
            "positive": len(positive),
            "negative": negative,
            "satisfaction_rate": satisfaction_rate
        }
