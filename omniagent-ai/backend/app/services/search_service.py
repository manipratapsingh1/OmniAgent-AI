from sqlmodel import Session, select
from app.models.conversation import Conversation
from app.models.message import Message
from datetime import datetime, timedelta
from typing import List, Dict
import structlog

log = structlog.get_logger("search")


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search_conversations(self, user_id: int, query: str, limit: int = 20) -> List[Conversation]:
        """Search user's conversations by title"""
        conversations = self.db.exec(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.title.ilike(f"%{query}%")
            )
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        ).all()
        
        log.info("search.conversations", user_id=user_id, query=query, results=len(conversations))
        return conversations

    def search_messages(self, user_id: int, query: str, limit: int = 50) -> List[Message]:
        """Search user's messages by content"""
        from app.models.conversation import Conversation
        
        messages = self.db.exec(
            select(Message)
            .join(Conversation)
            .where(
                Conversation.user_id == user_id,
                Message.content.ilike(f"%{query}%")
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        ).all()
        
        log.info("search.messages", user_id=user_id, query=query, results=len(messages))
        return messages

    def get_recent_conversations(self, user_id: int, days: int = 7, limit: int = 10) -> List[Conversation]:
        """Get recent conversations from last N days"""
        since = datetime.utcnow() - timedelta(days=days)
        
        conversations = self.db.exec(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.updated_at >= since
            )
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        ).all()
        
        return conversations

    def get_conversation_stats(self, user_id: int) -> Dict:
        """Get conversation statistics"""
        total = self.db.exec(
            select(Conversation).where(Conversation.user_id == user_id)
        ).all()
        
        recent = self.get_recent_conversations(user_id, days=30)
        
        return {
            "total_conversations": len(total),
            "recent_conversations_30d": len(recent),
        }
