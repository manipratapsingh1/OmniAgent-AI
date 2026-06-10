"""
Production configuration for OmniAgent AI
Optimized settings for performance and reliability
"""
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Production settings with optimizations"""
    
    # Application
    APP_NAME: str = "OmniAgent AI"
    APP_VERSION: str = "2.0.0"
    ENV: str = os.getenv("ENV", "production")
    DEBUG: bool = ENV == "development"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("PORT", "8000"))
    API_WORKERS: int = int(os.getenv("WORKERS", "4"))
    API_TIMEOUT: int = 300  # 5 minutes for long-running requests
    
    # Database - Optimized connection pool
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/omniagent")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600  # Recycle connections every hour
    DATABASE_ECHO: bool = False
    
    # Redis - Session and cache storage
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = 10
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    # LLM - Ollama settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    OLLAMA_TIMEOUT: int = 120  # 2 minutes timeout
    OLLAMA_FAST_MODEL: str = "phi3:mini"  # Fast model for quick responses
    
    # Vector database - Chroma
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_TIMEOUT: int = 10
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440  # 24 hours
    API_KEY_EXPIRY_DAYS: int = 90
    
    # Cors
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # Performance optimization
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default cache TTL
    CACHE_MAX_SIZE: int = 1000  # Max cached items
    RESPONSE_CACHE_ENABLED: bool = True
    QUERY_CACHE_ENABLED: bool = True
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Async settings
    ENABLE_ASYNC: bool = True
    ASYNCIO_POOL_SIZE: int = 10
    
    # Celery background jobs
    ENABLE_CELERY: bool = os.getenv("ENABLE_CELERY", "false").lower() == "true"
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # Use JSON for production logging
    
    # Memory settings
    SHORT_TERM_MEMORY_TTL_SECONDS: int = 3600  # 1 hour
    LONG_TERM_MEMORY_TTL_SECONDS: int = 2592000  # 30 days
    MAX_CONVERSATION_HISTORY: int = 100
    
    # Document processing
    MAX_DOCUMENT_SIZE_MB: int = 50
    ALLOWED_DOCUMENT_TYPES: list = [".pdf", ".txt", ".md", ".docx"]
    MAX_DOCUMENTS_PER_USER: int = 1000
    
    # RAG optimization
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_RETRIEVAL_LIMIT: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.3
    RAG_CACHE_ENABLED: bool = True
    
    # API quotas
    DEFAULT_USER_QUOTA: int = 1000
    ADMIN_QUOTA: int = 10000
    QUOTA_RESET_DAY: int = 1  # Reset on 1st of month
    
    # Feature flags
    ENABLE_ADMIN_API: bool = True
    ENABLE_API_KEYS: bool = True
    ENABLE_NOTIFICATIONS: bool = True
    ENABLE_AUDIT_LOG: bool = True
    ENABLE_SEARCH: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    This ensures settings are only loaded once
    """
    return Settings()


# Production-specific middleware settings
MIDDLEWARE_CONFIG = {
    "cors": {
        "allow_origins": get_settings().CORS_ORIGINS,
        "allow_credentials": get_settings().CORS_CREDENTIALS,
        "allow_methods": get_settings().CORS_METHODS,
        "allow_headers": get_settings().CORS_HEADERS,
    },
    "rate_limit": {
        "enabled": get_settings().RATE_LIMIT_ENABLED,
        "requests": get_settings().RATE_LIMIT_REQUESTS,
        "window_seconds": get_settings().RATE_LIMIT_WINDOW_SECONDS,
    },
    "compression": {
        "enabled": True,
        "minimum_size": 1000,  # Only compress responses > 1KB
    },
}


# Database optimization settings
DB_OPTIMIZATION = {
    "pool_size": get_settings().DATABASE_POOL_SIZE,
    "max_overflow": get_settings().DATABASE_MAX_OVERFLOW,
    "pool_timeout": get_settings().DATABASE_POOL_TIMEOUT,
    "pool_recycle": get_settings().DATABASE_POOL_RECYCLE,
    "echo": get_settings().DATABASE_ECHO,
    "connect_args": {
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
    },
}


# LLM optimization settings
LLM_OPTIMIZATION = {
    "request_timeout": get_settings().OLLAMA_TIMEOUT,
    "streaming_enabled": True,
    "context_window": 2048,
    "batch_size": 1,
    "temperature": 0.7,
    "top_p": 0.9,
}


# Cache configuration
CACHE_CONFIG = {
    "enabled": get_settings().RESPONSE_CACHE_ENABLED,
    "ttl": get_settings().CACHE_TTL_SECONDS,
    "max_size": get_settings().CACHE_MAX_SIZE,
}
