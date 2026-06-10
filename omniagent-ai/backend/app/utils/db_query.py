"""
Query utilities for database operations
"""
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from sqlmodel import Session, select
from sqlalchemy import and_, or_

T = TypeVar("T")


class QueryBuilder(Generic[T]):
    """Query builder for fluent SQLModel queries"""
    
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model
        self.stmt = select(model)
        self._filters = []
    
    def where(self, condition) -> "QueryBuilder[T]":
        """Add WHERE clause"""
        self._filters.append(condition)
        return self
    
    def filter_by(self, **kwargs) -> "QueryBuilder[T]":
        """Filter by field=value pairs"""
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key) == value)
        return self
    
    def order_by(self, *columns) -> "QueryBuilder[T]":
        """Add ORDER BY clause"""
        self.stmt = self.stmt.order_by(*columns)
        return self
    
    def limit(self, limit: int) -> "QueryBuilder[T]":
        """Add LIMIT clause"""
        self.stmt = self.stmt.limit(limit)
        return self
    
    def offset(self, offset: int) -> "QueryBuilder[T]":
        """Add OFFSET clause"""
        self.stmt = self.stmt.offset(offset)
        return self
    
    def build(self):
        """Build final statement with filters"""
        if self._filters:
            self.stmt = self.stmt.where(and_(*self._filters))
        return self.stmt
    
    def all(self) -> List[T]:
        """Execute and return all results"""
        return self.session.exec(self.build()).all()
    
    def first(self) -> Optional[T]:
        """Execute and return first result"""
        return self.session.exec(self.build().limit(1)).first()
    
    def count(self) -> int:
        """Execute and return count"""
        return len(self.all())
    
    def exists(self) -> bool:
        """Check if any results exist"""
        return self.first() is not None


def paginate(session: Session, model: Type[T], filters: Dict[str, Any] = None, 
             limit: int = 50, offset: int = 0, order_by = None) -> tuple[List[T], int]:
    """
    Generic pagination helper
    Returns: (items, total_count)
    """
    stmt = select(model)
    
    # Apply filters
    if filters:
        conditions = [getattr(model, k) == v for k, v in filters.items()]
        stmt = stmt.where(and_(*conditions))
    
    # Get total count
    total = len(session.exec(stmt).all())
    
    # Apply pagination
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    
    stmt = stmt.offset(offset).limit(limit)
    items = session.exec(stmt).all()
    
    return items, total
