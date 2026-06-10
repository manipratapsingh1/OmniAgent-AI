from typing import TypeVar, Generic, Type, Optional
from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepo(Generic[T]):
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get(self, id: int) -> Optional[T]:
        return self.session.get(self.model, id)

    def add(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def update(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        obj = self.session.get(self.model, id)
        if not obj:
            return False
        self.session.delete(obj)
        self.session.commit()
        return True

    def list(self, **filters):
        stmt = select(self.model)
        for k, v in filters.items():
            stmt = stmt.where(getattr(self.model, k) == v)
        return self.session.exec(stmt).all()

    def get_all(self, skip: int = 0, limit: int = 100):
        """Get all items with pagination"""
        stmt = select(self.model).offset(skip).limit(limit)
        return self.session.exec(stmt).all()