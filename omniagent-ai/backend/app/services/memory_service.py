from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlmodel import Session, select, delete
from app.models.memory import MemoryEntry, LearnedFact
import structlog
from sqlalchemy import func

log = structlog.get_logger("memory")


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def store_short_term(self, user_id: int, content: str, ttl: int = 3600):
        """Store short-term memory (1 hour default)"""
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        
        entry = MemoryEntry(
            user_id=user_id,
            memory_type="short_term",
            content=content,
            ttl=ttl,
            expires_at=expires_at
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        
        log.info("memory.short_term.stored", user_id=user_id, memory_id=entry.id)
        return entry

    def store_long_term(self, user_id: int, content: str, embedding: Optional[List[float]] = None):
        """Store long-term memory (persistent)"""
        entry = MemoryEntry(
            user_id=user_id,
            memory_type="long_term",
            content=content,
            embedding=embedding
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        # Also write long-term memory into the vector store for semantic recall
        try:
            if embedding:
                from app.rag.retriever import vector_store

                vector_store.add(
                    ids=[f"memory:{entry.id}"],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[{
                        "user_id": user_id,
                        "memory_type": "long_term",
                        "memory_id": entry.id,
                        "created_at": entry.created_at.isoformat(),
                    }],
                )
        except Exception as e:
            log.warning("memory.vector_store_index_failed", user_id=user_id, memory_id=entry.id, error=str(e))
        
        log.info("memory.long_term.stored", user_id=user_id, memory_id=entry.id)
        return entry

    def get_counts(self, user_id: Optional[int] = None):
        """Get short-term and long-term memory counts."""
        stmt = select(MemoryEntry)
        if user_id is not None:
            stmt = stmt.where(MemoryEntry.user_id == user_id)

        entries = self.db.exec(stmt).all()
        counts = {"short_term": 0, "long_term": 0}
        for entry in entries:
            if entry.memory_type == "long_term":
                counts["long_term"] += 1
            else:
                counts["short_term"] += 1
        return counts

    def get_short_term(self, user_id: int, limit: int = 10):
        """Get recent short-term memories"""
        try:
            entries = self.db.exec(
                select(MemoryEntry)
                .where(
                    MemoryEntry.user_id == user_id,
                    MemoryEntry.memory_type == "short_term",
                    MemoryEntry.expires_at > datetime.now(timezone.utc)
                )
                .order_by(MemoryEntry.created_at.desc())
                .limit(limit)
            ).all()
            log.debug("memory.short_term.retrieved", user_id=user_id, count=len(entries))
            return entries
        except Exception as e:
            log.error("memory.short_term.error", user_id=user_id, error=str(e))
            return []

    def get_long_term(self, user_id: int, limit: int = 50):
        """Get long-term memories"""
        try:
            entries = self.db.exec(
                select(MemoryEntry)
                .where(
                    MemoryEntry.user_id == user_id,
                    MemoryEntry.memory_type == "long_term"
                )
                .order_by(MemoryEntry.created_at.desc())
                .limit(limit)
            ).all()
            log.debug("memory.long_term.retrieved", user_id=user_id, count=len(entries))
            return entries
        except Exception as e:
            log.error("memory.long_term.error", user_id=user_id, error=str(e))
            return []

    def store_learned_fact(self, user_id: int, fact: str, category: str = "preference"):
        """Store a learned fact about the user."""
        existing = self.db.exec(
            select(LearnedFact)
            .where(LearnedFact.user_id == user_id, LearnedFact.fact == fact)
        ).first()
        
        if existing:
            existing.updated_at = datetime.now(timezone.utc)
            self.db.add(existing)
        else:
            entry = LearnedFact(user_id=user_id, fact=fact, category=category)
            self.db.add(entry)
            
        self.db.commit()
        log.info("memory.fact.stored", user_id=user_id, fact=fact[:50])

    def get_learned_facts(self, user_id: int, limit: int = 20):
        """Retrieve all learned facts for a user."""
        return self.db.exec(
            select(LearnedFact)
            .where(LearnedFact.user_id == user_id)
            .order_by(LearnedFact.updated_at.desc())
            .limit(limit)
        ).all()

    def search_memories(self, user_id: int, query: str, limit: int = 10):
        """Search memories by content"""
        try:
            entries = self.db.exec(
                select(MemoryEntry)
                .where(
                    MemoryEntry.user_id == user_id,
                    MemoryEntry.content.ilike(f"%{query}%")
                )
                .order_by(MemoryEntry.created_at.desc())
                .limit(limit)
            ).all()
            log.debug("memory.search.results", user_id=user_id, query=query, count=len(entries))
            return entries
        except Exception as e:
            log.error("memory.search.error", user_id=user_id, query=query, error=str(e))
            return []

    def cleanup_expired(self):
        """Remove expired short-term memories"""
        try:
            stmt = delete(MemoryEntry).where(
                (MemoryEntry.memory_type == "short_term") &
                (MemoryEntry.expires_at < datetime.now(timezone.utc))
            )
            result = self.db.exec(stmt)
            self.db.commit()
            log.info("memory.cleanup.completed", deleted_count=result.rowcount if hasattr(result, 'rowcount') else 0)
        except Exception as e:
            self.db.rollback()
            log.error("memory.cleanup.error", error=str(e))
