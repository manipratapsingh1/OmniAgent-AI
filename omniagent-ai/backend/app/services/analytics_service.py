from sqlmodel import Session, select, func
from app.models.message import Message
from app.models.agent_run import AgentRun
from app.models.user import User
from app.models.document import Document
from app.models.document_tags import DocumentTag
from datetime import datetime, timedelta, timezone
import structlog

log = structlog.get_logger("analytics")


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def overview(self) -> dict:
        users = self.db.exec(select(func.count(User.id))).one()
        msgs = self.db.exec(select(func.count(Message.id))).one()
        runs = self.db.exec(select(func.count(AgentRun.id))).one()
        avg_lat = self.db.exec(select(func.avg(AgentRun.latency_ms))).one() or 0
        
        return {
            "users": int(users or 0),
            "messages": int(msgs or 0),
            "agent_runs": int(runs or 0),
            "avg_agent_latency_ms": float(avg_lat or 0),
        }

    def get_user_analytics(self) -> dict:
        """Get user statistics"""
        total_users = self.db.exec(select(func.count(User.id))).one() or 0
        active_users = self.db.exec(select(func.count(User.id)).where(User.is_active == True)).one() or 0
        admin_users = self.db.exec(select(func.count(User.id)).where(User.is_admin == True)).one() or 0
        
        return {
            "total_users": int(total_users),
            "active_users": int(active_users),
            "admin_users": int(admin_users)
        }

    def get_document_analytics(self) -> dict:
        """Get document statistics"""
        total_docs = self.db.exec(select(func.count(Document.id))).one() or 0
        indexed_docs = self.db.exec(
            select(func.count(Document.id)).where(Document.status == "indexed")
        ).one() or 0
        failed_docs = self.db.exec(
            select(func.count(Document.id)).where(Document.status == "failed")
        ).one() or 0
        pending_docs = self.db.exec(
            select(func.count(Document.id)).where(Document.status == "pending")
        ).one() or 0
        
        total_size = self.db.exec(
            select(func.sum(Document.size_bytes))
        ).one() or 0
        
        return {
            "total_documents": int(total_docs),
            "indexed": int(indexed_docs),
            "failed": int(failed_docs),
            "pending": int(pending_docs),
            "total_size_bytes": int(total_size),
        }

    def get_message_analytics(self) -> dict:
        """Get message statistics"""
        total_messages = self.db.exec(select(func.count(Message.id))).one() or 0
        user_messages = self.db.exec(select(func.count(Message.id)).where(Message.role == "user")).one() or 0
        assistant_messages = self.db.exec(select(func.count(Message.id)).where(Message.role == "assistant")).one() or 0
        
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        messages_last_24h = self.db.exec(
            select(func.count(Message.id)).where(Message.created_at >= yesterday)
        ).one() or 0
        
        return {
            "total_messages": int(total_messages),
            "user_messages": int(user_messages),
            "assistant_messages": int(assistant_messages),
            "messages_last_24h": int(messages_last_24h)
        }

    def get_agent_analytics(self) -> dict:
        """Get agent run statistics"""
        total_runs = self.db.exec(select(func.count(AgentRun.id))).one() or 0
        avg_latency = self.db.exec(select(func.avg(AgentRun.latency_ms))).one() or 0
        
        # Popular agents
        agent_usage = self.db.exec(
            select(AgentRun.agent, func.count(AgentRun.id).label("count"))
            .group_by(AgentRun.agent)
            .order_by(func.count(AgentRun.id).desc())
            .limit(5)
        ).all()
        
        # Success rate (assume any run with latency > 0 is a success for now, 
        # or we could add a success field to AgentRun)
        success_rate = 1.0 if total_runs > 0 else 0.0
        
        return {
            "total_runs": int(total_runs),
            "avg_latency_ms": float(avg_latency or 0),
            "success_rate": success_rate,
            "popular_agents": [
                {"agent": item[0], "count": int(item[1] or 0)} for item in agent_usage
            ]
        }

    def get_tag_usage_analytics(self, days: int = 30) -> dict:
        """Get top tags and category usage for documents."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        tag_counts = self.db.exec(
            select(DocumentTag.tag, func.count(DocumentTag.id).label("count"))
            .where(DocumentTag.created_at >= cutoff)
            .group_by(DocumentTag.tag)
            .order_by(func.count(DocumentTag.id).desc())
            .limit(12)
        ).all()

        category_counts = self.db.exec(
            select(DocumentTag.category, func.count(DocumentTag.id).label("count"))
            .where(DocumentTag.created_at >= cutoff)
            .group_by(DocumentTag.category)
            .order_by(func.count(DocumentTag.id).desc())
            .limit(12)
        ).all()

        return {
            "top_tags": [
                {"tag": item[0], "count": int(item[1] or 0)} for item in tag_counts
            ],
            "top_categories": [
                {"category": item[0] or "Uncategorized", "count": int(item[1] or 0)} for item in category_counts
            ],
        }

    def get_full_dashboard(self) -> dict:
        """Get complete dashboard analytics"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overview": self.overview(),
            "users": self.get_user_analytics(),
            "documents": self.get_document_analytics(),
            "messages": self.get_message_analytics(),
            "agents": self.get_agent_analytics(),
        }