from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "OmniAgent AI"
    APP_ENV: str = "dev"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    SECRET_KEY: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    VECTOR_BACKEND: str = "chroma"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2"
    OLLAMA_FAST_MODEL: str = "phi3:mini"  # Fast model for low-latency chat
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    RATE_LIMIT_PER_MINUTE: int = 120  # Increased from 60 to allow for polling and retries
    CORS_ORIGINS: str = "http://localhost:5173"
    
    # New feature settings
    ENABLE_CELERY: bool = False
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # API Keys
    API_KEY_EXPIRY_DAYS: int = 365
    
    # Memory settings
    SHORT_TERM_MEMORY_TTL: int = 3600  # 1 hour
    LONG_TERM_MEMORY_LIMIT: int = 1000  # max entries
    
    # RAG settings
    MAX_DOCUMENT_SIZE_MB: int = 10
    MAX_CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 120
    RETRIEVAL_TOP_K: int = 5
    
    # Performance timeouts
    OLLAMA_EMBED_TIMEOUT: int = 30  # seconds - shorter for fail-fast retries
    OLLAMA_GENERATE_TIMEOUT: int = 60  # seconds
    FAST_RAG_MODEL: str = "phi3:mini"  # Fast model for RAG queries
    
    # Notifications
    ENABLE_WEBSOCKETS: bool = True
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    # Monitoring
    ENABLE_SENTRY: bool = False
    SENTRY_DSN: str = ""
    # Assistant feature flag
    ASSISTANT_ENABLED: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]