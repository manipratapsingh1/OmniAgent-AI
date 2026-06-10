from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.deps import db_session, current_user
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserOut, PasswordChangeRequest
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
def signup(data: SignupRequest, db: Session = Depends(db_session)):
    return AuthService(db).signup(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(db_session)):
    return AuthService(db).login(data)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, is_admin=user.is_admin)


@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_token: str, db: Session = Depends(db_session)):
    return AuthService(db).refresh_token(refresh_token)


@router.post("/change-password")
def change_password(data: PasswordChangeRequest, db: Session = Depends(db_session), user: User = Depends(current_user)):
    return AuthService(db).change_password(user, data)