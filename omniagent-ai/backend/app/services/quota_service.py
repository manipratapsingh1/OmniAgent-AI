from sqlmodel import Session, select
from app.models.user import User
from datetime import datetime, timedelta
import structlog

log = structlog.get_logger("quota")


class QuotaService:
    def __init__(self, db: Session):
        self.db = db

    def check_user_quota(self, user_id: int) -> dict:
        """Check if user has remaining quota"""
        user = self.db.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if not user:
            return {"has_quota": False, "message": "User not found"}
        
        remaining = user.api_quota - user.api_used
        percentage = (user.api_used / user.api_quota * 100) if user.api_quota > 0 else 0
        
        return {
            "has_quota": remaining > 0,
            "used": user.api_used,
            "quota": user.api_quota,
            "remaining": remaining,
            "usage_percentage": percentage
        }

    def increment_usage(self, user_id: int, count: int = 1) -> bool:
        """Increment API usage counter"""
        user = self.db.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if not user:
            return False
        
        quota_check = self.check_user_quota(user_id)
        if not quota_check["has_quota"]:
            log.warning("quota.exceeded", user_id=user_id)
            return False
        
        user.api_used += count
        self.db.add(user)
        self.db.commit()
        
        log.info("quota.incremented", user_id=user_id, new_usage=user.api_used)
        return True

    def reset_monthly_quota(self, user_id: int = None) -> int:
        """Reset API usage (call monthly via cron)"""
        if user_id:
            user = self.db.exec(
                select(User).where(User.id == user_id)
            ).first()
            if user:
                user.api_used = 0
                self.db.add(user)
                self.db.commit()
                return 1
        else:
            # Reset all users
            users = self.db.exec(select(User)).all()
            for user in users:
                user.api_used = 0
                self.db.add(user)
            self.db.commit()
            log.info("quota.monthly_reset", users_reset=len(users))
            return len(users)

    def get_user_stats(self, user_id: int) -> dict:
        """Get comprehensive user API usage stats"""
        quota = self.check_user_quota(user_id)
        
        return {
            "user_id": user_id,
            "quota": quota["quota"],
            "used": quota["used"],
            "remaining": quota["remaining"],
            "usage_percentage": quota["usage_percentage"],
            "status": "active" if quota["has_quota"] else "quota_exceeded"
        }
