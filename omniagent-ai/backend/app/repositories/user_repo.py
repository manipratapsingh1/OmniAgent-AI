from typing import Optional
from sqlmodel import Session, select
from app.models.user import User
from app.repositories.base import BaseRepo


class UserRepo(BaseRepo[User]):
    def __init__(self, session: Session):
        super().__init__(User, session)

    def by_email(self, email: str) -> Optional[User]:
        return self.session.exec(select(User).where(User.email == email)).first()