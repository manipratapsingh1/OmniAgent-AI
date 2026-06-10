from sqlmodel import create_engine, Session, select
from sqlalchemy.pool import StaticPool, NullPool, QueuePool
from app.config import get_settings
import structlog

log = structlog.get_logger("db")

_settings = get_settings()

# Validate DATABASE_URL exists
if not _settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is required. Please set it in .env file")

db_type = _settings.DATABASE_URL.split("://")[0]
log.info("db.config", database_url=db_type)

# Configure pooling based on database type
if "sqlite" in _settings.DATABASE_URL:
    # SQLite: disable pooling, enable WAL mode for better concurrency
    engine = create_engine(
        _settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # SQLite works better without connection pooling
        connect_args={"timeout": 30, "check_same_thread": False},
    )
    # Enable WAL mode for SQLite for better concurrent access
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            conn.exec_driver_sql("PRAGMA busy_timeout=30000")  # 30 second timeout
    except Exception as e:
        log.warning("db.wal_mode.failed", error=str(e))
else:
    # PostgreSQL or other databases: use connection pooling
    engine = create_engine(
        _settings.DATABASE_URL,
        echo=False,
        poolclass=QueuePool,  # Use QueuePool for better handling
        pool_pre_ping=True,  # Verify connection is alive before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_size=20,  # Number of connections to keep in pool
        max_overflow=40,  # Max additional connections beyond pool_size
        pool_timeout=30,  # Wait up to 30 seconds for a connection
    )


def get_session() -> Session:
    """Get a new database session"""
    return Session(engine)


def get_session_sync() -> Session:
    """Get a new database session (sync helper)"""
    return get_session()


def get_session_context():
    """Get a session as a context manager for use in dependencies"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def test_db_connection() -> bool:
    """Test if database connection is working"""
    try:
        session = Session(engine)
        session.exec(select(1)).first()
        session.close()
        log.info("db.connection.ok")
        return True
    except Exception as e:
        log.error("db.connection.failed", error=str(e))
        return False