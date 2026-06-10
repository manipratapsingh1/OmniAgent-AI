"""
Database connection diagnostics and debugging utilities
"""

import structlog
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ArgumentError
from app.config import get_settings

log = structlog.get_logger("db_diagnostics")


def get_database_connection_error_message(error: Exception) -> str:
    """Convert database errors into helpful user messages"""
    
    error_str = str(error).lower()
    settings = get_settings()
    
    # Parse PostgreSQL connection string
    try:
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        database = parsed.path.lstrip("/") or "postgres"
        user = parsed.username or "postgres"
    except:
        host = "localhost"
        port = 5432
        database = "unknown"
        user = "postgres"
    
    if isinstance(error, OperationalError):
        if "connection refused" in error_str or "refused" in error_str:
            return (
                f"PostgreSQL is not running or not accessible at {host}:{port}\n"
                f"Expected DATABASE_URL: {settings.DATABASE_URL}\n"
                f"Please ensure:\n"
                f"  1. PostgreSQL is running\n"
                f"  2. Database '{database}' exists\n"
                f"  3. User '{user}' can connect\n"
                f"  4. Credentials in .env are correct"
            )
        elif "authentication failed" in error_str or "password" in error_str:
            return (
                f"PostgreSQL authentication failed for user '{user}' at {host}:{port}\n"
                f"Please verify credentials in .env file:\n"
                f"  DATABASE_URL={settings.DATABASE_URL}"
            )
        elif "database" in error_str and "does not exist" in error_str:
            return (
                f"Database '{database}' does not exist on {host}:{port}\n"
                f"Please create the database:\n"
                f"  createdb -h {host} -U {user} {database}"
            )
    
    elif isinstance(error, ArgumentError):
        return (
            f"Invalid DATABASE_URL format in .env file\n"
            f"Current value: {settings.DATABASE_URL}\n"
            f"Expected format: postgresql://user:password@host:port/database"
        )
    
    return f"Database connection error: {str(error)}"


def diagnose_database_connection():
    """Perform detailed database connection diagnostics"""
    
    settings = get_settings()
    results = {
        "database_url_set": bool(settings.DATABASE_URL),
        "database_url": settings.DATABASE_URL[:20] + "..." if settings.DATABASE_URL else "NOT SET",
        "connection_successful": False,
        "error": None,
    }
    
    if not settings.DATABASE_URL:
        results["error"] = "DATABASE_URL not set in .env file"
        return results
    
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            results["connection_successful"] = True
            log.info("database.connection.successful")
    except Exception as e:
        results["error"] = get_database_connection_error_message(e)
        log.error("database.connection.failed", error=str(e))
    
    return results
