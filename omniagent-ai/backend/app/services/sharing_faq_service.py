"""Conversation sharing and FAQ services."""

from typing import List, Dict, Any, Optional
import structlog
import secrets
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select

from app.models.sharing_and_faq import ConversationShare, FrequentlyAskedQuestion, QueryTemplate

log = structlog.get_logger("sharing_faq_service")


class SharingAndFAQService:
    """Handle conversation sharing and FAQ management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_share(
        self,
        conversation_id: int,
        shared_by_user_id: int,
        shared_with_user_id: Optional[int] = None,
        expires_in_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a shareable link for a conversation."""
        try:
            share_token = secrets.token_urlsafe(32)
            expires_at = None
            
            if expires_in_hours:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
            
            share = ConversationShare(
                conversation_id=conversation_id,
                shared_by_user_id=shared_by_user_id,
                shared_with_user_id=shared_with_user_id,
                share_token=share_token,
                expires_at=expires_at,
            )
            
            self.db.add(share)
            self.db.commit()
            self.db.refresh(share)
            
            log.info("sharing.created", conversation_id=conversation_id)
            
            return {
                "share_token": share_token,
                "share_url": f"/shared/{share_token}",
                "expires_at": expires_at.isoformat() if expires_at else None,
            }
        except Exception as e:
            log.error("sharing.create_failed", error=str(e))
            raise
    
    async def access_shared_conversation(self, share_token: str) -> Optional[Dict[str, Any]]:
        """Access a shared conversation via token."""
        try:
            share = self.db.exec(
                select(ConversationShare).where(ConversationShare.share_token == share_token)
            ).first()
            
            if not share:
                return None
            
            # Check expiration
            if share.expires_at and share.expires_at < datetime.now(timezone.utc):
                return None
            
            # Increment access count
            share.access_count += 1
            self.db.add(share)
            self.db.commit()
            
            log.info("sharing.accessed", share_token=share_token)
            
            return {
                "conversation_id": share.conversation_id,
                "access_count": share.access_count,
            }
        except Exception as e:
            log.error("sharing.access_failed", error=str(e))
            return None
    
    async def add_faq(
        self,
        document_id: int,
        question: str,
        answer: str,
        relevance_score: float = 0.8,
    ) -> Dict[str, Any]:
        """Add an FAQ entry from a document."""
        try:
            faq = FrequentlyAskedQuestion(
                document_id=document_id,
                question=question,
                answer=answer,
                relevance_score=relevance_score,
            )
            
            self.db.add(faq)
            self.db.commit()
            self.db.refresh(faq)
            
            log.info("faq.added", document_id=document_id)
            
            return {
                "id": faq.id,
                "question": faq.question,
                "status": "added",
            }
        except Exception as e:
            log.error("faq.add_failed", error=str(e))
            raise
    
    async def get_document_faqs(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all FAQs for a document."""
        try:
            faqs = self.db.exec(
                select(FrequentlyAskedQuestion).where(
                    FrequentlyAskedQuestion.document_id == document_id
                )
            ).all()
            
            return [
                {
                    "id": f.id,
                    "question": f.question,
                    "answer": f.answer,
                    "relevance_score": f.relevance_score,
                }
                for f in faqs
            ]
        except Exception as e:
            log.error("faq.get_failed", error=str(e))
            return []
    
    async def create_query_template(
        self,
        title: str,
        template: str,
        category: str,
        icon: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a query template."""
        try:
            qt = QueryTemplate(
                title=title,
                template=template,
                category=category,
                icon=icon,
            )
            
            self.db.add(qt)
            self.db.commit()
            self.db.refresh(qt)
            
            log.info("template.created", title=title)
            
            return {
                "id": qt.id,
                "title": qt.title,
                "status": "created",
            }
        except Exception as e:
            log.error("template.create_failed", error=str(e))
            raise
    
    async def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get query templates by category."""
        try:
            templates = self.db.exec(
                select(QueryTemplate).where(QueryTemplate.category == category)
            ).all()
            
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "template": t.template,
                    "icon": t.icon,
                    "usage_count": t.usage_count,
                }
                for t in templates
            ]
        except Exception as e:
            log.error("template.get_failed", error=str(e))
            return []
