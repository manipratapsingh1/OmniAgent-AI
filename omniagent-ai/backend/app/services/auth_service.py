import structlog
from sqlmodel import Session
from fastapi import HTTPException

from app.repositories.user_repo import UserRepo
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, PasswordChangeRequest
from app.utils.security import sanitize_email, sanitize_string, is_valid_password
from app.services.audit_service import AuditService

log = structlog.get_logger("auth")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepo(db)
        self.audit = AuditService(db)

    def signup(self, data: SignupRequest) -> TokenResponse:
        # Sanitize input
        email = sanitize_email(data.email)
        full_name = sanitize_string(data.full_name or "", max_length=256)

        if self.users.by_email(email):
            log.warning("signup.email_exists", email=email)
            raise HTTPException(status_code=400, detail="Email already registered")

        # Validate password
        is_valid, error_msg = is_valid_password(data.password)
        if not is_valid:
            log.warning("signup.invalid_password", email=email)
            raise HTTPException(status_code=400, detail=error_msg)

        user = User(email=email, hashed_password=hash_password(data.password), full_name=full_name if full_name else None)
        self.users.add(user)
        self.audit.log(action="signup", entity="user", user_id=user.id)
        log.info("signup.success", user_id=user.id, email=user.email)
        return TokenResponse(
            access_token=create_access_token(user.email),
            refresh_token=create_refresh_token(user.email)
        )

    def login(self, data: LoginRequest) -> TokenResponse:
        email = sanitize_email(data.email)
        user = self.users.by_email(email)
        if not user or not verify_password(data.password, user.hashed_password):
            self.audit.log(action="login_failed", entity="user", meta={"email": email})
            log.warning("login.failed", email=email)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        self.audit.log(action="login", entity="user", user_id=user.id)
        log.info("login.success", user_id=user.id, email=user.email)
        return TokenResponse(
            access_token=create_access_token(user.email),
            refresh_token=create_refresh_token(user.email)
        )

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Issue new access token from refresh token"""
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            email = payload.get("sub")
            if not email:
                raise HTTPException(status_code=401, detail="Invalid token payload")
                
            user = self.users.by_email(email)
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
                
            new_refresh = create_refresh_token(user.email)
            log.info("token.refreshed", user_id=user.id, email=user.email)
            return TokenResponse(
                access_token=create_access_token(user.email),
                refresh_token=new_refresh
            )
        except Exception as e:
            log.warning("token.refresh_failed", error=str(e))
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    def change_password(self, user: User, data: PasswordChangeRequest) -> dict:
        """Change user password"""
        if not verify_password(data.current_password, user.hashed_password):
            log.warning("change_password.invalid_current", user_id=user.id)
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # Validate new password
        is_valid, error_msg = is_valid_password(data.new_password)
        if not is_valid:
            log.warning("change_password.invalid_new", user_id=user.id)
            raise HTTPException(status_code=400, detail=error_msg)
        
        user.hashed_password = hash_password(data.new_password)
        self.users.add(user)
        log.info("change_password.success", user_id=user.id)
        return {"message": "Password changed successfully"}