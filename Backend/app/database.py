"""
Database configuration and models for OmniAgent AI
"""
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omniai.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============= MODELS =============

class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    documents = relationship("Document", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    
    # User statistics
    total_conversations = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)


class UserPreference(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    tone = Column(String, default="professional")  # professional, casual, formal
    expertise_level = Column(String, default="intermediate")  # beginner, intermediate, expert
    preferred_tools = Column(JSON, default=list)
    custom_instructions = Column(Text, nullable=True)
    dark_mode = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="preferences")


class Conversation(Base):
    """Chat conversation history"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    total_messages = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    tokens_used = Column(Integer, default=0)
    sources = Column(JSON, default=list)  # For RAG sources
    
    conversation = relationship("Conversation", back_populates="messages")


class Document(Base):
    """Uploaded documents for RAG"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    filename = Column(String)
    content_type = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Vector DB metadata
    vector_db_id = Column(String, nullable=True)
    chunk_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="documents")


class Task(Base):
    """Task management"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=3)  # 1-5, higher = more priority
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    
    # Recurrence
    recurrence = Column(String, nullable=True)  # daily, weekly, monthly, yearly
    is_recurring = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="tasks")


class APILog(Base):
    """API request/response logging"""
    __tablename__ = "api_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    endpoint = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    
    request_data = Column(JSON, nullable=True)
    response_time = Column(Float)  # in seconds
    
    created_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)


class AuditLog(Base):
    """Audit trail for important operations"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(String)
    
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
