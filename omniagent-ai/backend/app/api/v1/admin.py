from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

from app.deps import db_session, require_admin
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.repositories.user_repo import UserRepo
import structlog

log = structlog.get_logger("admin")

router = APIRouter()


class UserStats(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    api_quota: int
    api_used: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class UpdateRoleRequest(BaseModel):
    role: str


class UpdateQuotaRequest(BaseModel):
    quota: int


class ToggleActiveRequest(BaseModel):
    is_active: Optional[bool] = None


@router.get("/overview")
def overview(db: Session = Depends(db_session), _=Depends(require_admin)):
    """Get admin dashboard overview"""
    return AnalyticsService(db).overview()


@router.get("/dashboard")
def dashboard(db: Session = Depends(db_session), _=Depends(require_admin)):
    """Get full admin dashboard"""
    return AnalyticsService(db).get_full_dashboard()


@router.get("/metrics", response_model=Dict[str, Any])
def get_metrics(
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin)
):
    """Get system metrics"""
    from app.services.monitoring_service import MonitoringService
    return MonitoringService(db).get_full_report()


@router.get("/analytics/users")
def user_analytics(db: Session = Depends(db_session), _=Depends(require_admin)):
    """Get user analytics"""
    return AnalyticsService(db).get_user_analytics()


@router.get("/analytics/documents")
def document_analytics(db: Session = Depends(db_session), _=Depends(require_admin)):
    """Get document analytics"""
    return AnalyticsService(db).get_document_analytics()


@router.get("/analytics/messages")
def message_analytics(db: Session = Depends(db_session), _=Depends(require_admin)):
    """Get message analytics"""
    return AnalyticsService(db).get_message_analytics()


@router.get("/analytics/agents")
def agent_analytics(db: Session = Depends(db_session), _=Depends(require_admin)):
    """Get agent analytics"""
    return AnalyticsService(db).get_agent_analytics()


@router.get("/users", response_model=List[UserStats])
def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(db_session),
    _=Depends(require_admin)
):
    """List all users"""
    user_repo = UserRepo(db)
    users = user_repo.get_all(skip=skip, limit=limit)
    
    return [
        UserStats(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            api_quota=u.api_quota,
            api_used=u.api_used,
            created_at=u.created_at.isoformat()
        )
        for u in users
    ]


@router.put("/users/{user_id}/role", response_model=UserStats)
def update_user_role(
    user_id: int,
    request: UpdateRoleRequest,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin)
):
    """Update user role"""
    if request.role not in ["user", "moderator", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user_repo = UserRepo(db)
    user = user_repo.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = request.role
    user.is_admin = (request.role == "admin")
    user_repo.update(user)
    
    log.info("admin.user_role_updated", user_id=user_id, role=request.role, admin_id=admin.id)
    return UserStats(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        api_quota=user.api_quota,
        api_used=user.api_used,
        created_at=user.created_at.isoformat()
    )


@router.put("/users/{user_id}/quota", response_model=UserStats)
def update_user_quota(
    user_id: int,
    request: UpdateQuotaRequest,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin)
):
    """Update user API quota"""
    if request.quota < 0:
        raise HTTPException(status_code=400, detail="Quota must be positive")
    
    user_repo = UserRepo(db)
    user = user_repo.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.api_quota = request.quota
    user_repo.update(user)
    
    log.info("admin.quota_updated", user_id=user_id, quota=request.quota, admin_id=admin.id)
    return UserStats(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        api_quota=user.api_quota,
        api_used=user.api_used,
        created_at=user.created_at.isoformat()
    )


@router.put("/users/{user_id}/toggle-active", response_model=UserStats)
def toggle_user_active(
    user_id: int,
    request: Optional[ToggleActiveRequest] = None,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin)
):
    """Toggle or set user active status"""
    user_repo = UserRepo(db)
    user = user_repo.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If is_active is provided in the request, set it explicitly, otherwise toggle
    if request and request.is_active is not None:
        user.is_active = request.is_active
    else:
        user.is_active = not user.is_active
    
    user_repo.update(user)
    
    log.info("admin.user_toggled", user_id=user_id, is_active=user.is_active, admin_id=admin.id)
    return UserStats(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        api_quota=user.api_quota,
        api_used=user.api_used,
        created_at=user.created_at.isoformat()
    )