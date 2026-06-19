from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from app.deps import db_session, current_user
from app.models.user import User
from app.services.notification_service import NotificationService

router = APIRouter()


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    data: Optional[str]
    is_read: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


@router.get("/notifications", response_model=List[NotificationResponse])
def get_unread_notifications(
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Get unread notifications"""
    service = NotificationService(db)
    notifs = service.get_unread(user.id)
    
    return [
        NotificationResponse(
            id=n.id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            data=n.data,
            is_read=n.is_read,
            created_at=n.created_at.isoformat()
        )
        for n in notifs
    ]


@router.put("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Mark notification as read"""
    service = NotificationService(db)
    success = service.mark_as_read(notif_id, user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"status": "marked as read"}


@router.put("/notifications/read-all")
def mark_all_notifications_read(
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Mark all notifications as read"""
    service = NotificationService(db)
    service.mark_all_read(user.id)
    
    return {"status": "all marked as read"}
