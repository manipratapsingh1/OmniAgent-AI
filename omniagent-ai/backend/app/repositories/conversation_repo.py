from sqlmodel import Session, select, and_
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import BaseRepo
from typing import List, Tuple


class ConversationRepo(BaseRepo[Conversation]):
    def __init__(self, session: Session):
        super().__init__(Conversation, session)

    def for_user(self, user_id: int, limit: int = 50, offset: int = 0) -> Tuple[List[Conversation], int]:
        # Get total count
        stmt = select(Conversation).where(Conversation.user_id == user_id)
        total = len(self.session.exec(stmt).all())
        # Get paginated results
        stmt = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
        items = self.session.exec(stmt).all()
        return items, total

    def search(self, user_id: int, query: str) -> List[Conversation]:
        """Search conversations by title (case-insensitive)"""
        query_lower = query.lower()
        stmt = select(Conversation).where(
            (Conversation.user_id == user_id) &
            (Conversation.title.ilike(f"%{query_lower}%"))
        ).order_by(Conversation.updated_at.desc())
        return self.session.exec(stmt).all()

    def messages(self, conversation_id: int):
        return self.session.exec(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        ).all()

    def delete_messages(self, conversation_id: int) -> bool:
        """Delete all messages in a conversation"""
        messages = self.session.exec(select(Message).where(Message.conversation_id == conversation_id)).all()
        for msg in messages:
            self.session.delete(msg)
        self.session.commit()
        return True