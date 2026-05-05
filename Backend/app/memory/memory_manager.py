# backend/app/memory/memory_manager.py
"""
Long-Term Memory System - Stores conversations, preferences, and knowledge
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

Base = declarative_base()


class ConversationMemory(Base):
    """Stores conversation history"""
    __tablename__ = "conversation_memory"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    content = Column(Text)  # JSON serialized
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPreferences(Base):
    """Stores user preferences and personalization"""
    __tablename__ = "user_preferences"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, unique=True, index=True)
    preferences = Column(Text)  # JSON: {tone, expertise_level, preferred_tools, etc.}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeBase(Base):
    """Stores uploaded documents and knowledge"""
    __tablename__ = "knowledge_base"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    title = Column(String)
    content = Column(Text)  # Extracted text from PDF/document
    meta_data = Column(Text)  # JSON: {source, upload_date, file_type}
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryManager:
    """Manages all memory operations"""
    
    def __init__(self, db_url: str = "sqlite:///./omniai.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    # ============= CONVERSATION MEMORY =============
    def save_conversation(self, user_id: str, conversation_id: str, messages: List[Dict]):
        """Store conversation for later retrieval"""
        session = self.SessionLocal()
        try:
            memory = ConversationMemory(
                id=conversation_id,
                user_id=user_id,
                content=json.dumps(messages)
            )
            session.add(memory)
            session.commit()
        finally:
            session.close()
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve user's past conversations for context"""
        session = self.SessionLocal()
        try:
            conversations = session.query(ConversationMemory)\
                .filter(ConversationMemory.user_id == user_id)\
                .order_by(ConversationMemory.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [json.loads(c.content) for c in conversations]
        finally:
            session.close()
    
    # ============= USER PREFERENCES =============
    def save_preferences(self, user_id: str, preferences: Dict):
        """Store user preferences for personalization"""
        session = self.SessionLocal()
        try:
            prefs = session.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()
            
            if prefs:
                prefs.preferences = json.dumps(preferences)
                prefs.updated_at = datetime.utcnow()
            else:
                prefs = UserPreferences(
                    id=f"pref_{user_id}",
                    user_id=user_id,
                    preferences=json.dumps(preferences)
                )
                session.add(prefs)
            
            session.commit()
        finally:
            session.close()
    
    def get_preferences(self, user_id: str) -> Dict:
        """Retrieve user preferences"""
        session = self.SessionLocal()
        try:
            prefs = session.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()
            
            if prefs:
                return json.loads(prefs.preferences)
            return {}
        finally:
            session.close()
    
    # ============= KNOWLEDGE BASE =============
    def add_knowledge(self, user_id: str, title: str, content: str, meta_data: Dict):
        """Store document/knowledge"""
        session = self.SessionLocal()
        try:
            from uuid import uuid4
            knowledge = KnowledgeBase(
                id=str(uuid4()),
                user_id=user_id,
                title=title,
                content=content,
                meta_data=json.dumps(meta_data)
            )
            session.add(knowledge)
            session.commit()
        finally:
            session.close()
    
    def search_knowledge(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Search user's knowledge base"""
        session = self.SessionLocal()
        try:
            # Simple text search - upgrade to full-text search in production
            results = session.query(KnowledgeBase)\
                .filter(KnowledgeBase.user_id == user_id)\
                .filter(KnowledgeBase.content.ilike(f"%{query}%"))\
                .limit(limit)\
                .all()
            
            return [{
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "meta_data": json.loads(r.meta_data)
            } for r in results]
        finally:
            session.close()
    
    def get_all_knowledge(self, user_id: str) -> List[Dict]:
        """Get all knowledge for a user"""
        session = self.SessionLocal()
        try:
            results = session.query(KnowledgeBase)\
                .filter(KnowledgeBase.user_id == user_id)\
                .all()
            
            return [{
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "meta_data": json.loads(r.meta_data)
            } for r in results]
        finally:
            session.close()
