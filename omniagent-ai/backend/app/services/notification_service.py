from sqlmodel import Session, select
from app.models.notification import Notification
from datetime import datetime
import structlog

log = structlog.get_logger("notifications")


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, notification_type: str, title: str, message: str, data: str = None) -> Notification:
        """Create a new notification"""
        notif = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        
        log.info("notification.created", user_id=user_id, type=notification_type)
        return notif

    def get_unread(self, user_id: int):
        """Get unread notifications"""
        notifs = self.db.exec(
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .order_by(Notification.created_at.desc())
        ).all()
        return notifs

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        notif = self.db.exec(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
        
        if not notif:
            return False
        
        notif.is_read = True
        self.db.add(notif)
        self.db.commit()
        return True

    def mark_all_read(self, user_id: int):
        """Mark all notifications as read"""
        notifs = self.db.exec(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).all()
        
        for notif in notifs:
            notif.is_read = True
            self.db.add(notif)
        
        self.db.commit()
        log.info("notifications.marked_read", user_id=user_id, count=len(notifs))
