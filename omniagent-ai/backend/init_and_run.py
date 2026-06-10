#!/usr/bin/env python3
"""
Comprehensive initialization and startup script for OmniAgent API
Validates all requirements and starts the application
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

import structlog
from app.config import get_settings
from app.db.session import test_db_connection, engine
from app.db.init_db import init_db

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.get_logger("init")


def validate_config():
    """Validate all required configuration is present"""
    log.info("init.validating_config")
    
    try:
        settings = get_settings()
        
        # Check required settings
        required = [
            "SECRET_KEY",
            "DATABASE_URL",
            "CHROMA_HOST",
            "CHROMA_PORT",
            "OLLAMA_BASE_URL",
        ]
        
        missing = []
        for key in required:
            value = getattr(settings, key, None)
            if not value:
                missing.append(key)
            else:
                log.info(f"config.{key.lower()}", value=(value[:20] + "..." if len(str(value)) > 20 else value))
        
        if missing:
            log.error("config.missing_required", missing=missing)
            return False
        
        log.info("config.valid")
        return True
    except Exception as e:
        log.exception("config.error", error=str(e))
        return False


def test_database():
    """Test database connection"""
    log.info("init.testing_database")
    
    try:
        if test_db_connection():
            log.info("database.connected")
            return True
        else:
            log.error("database.connection_failed")
            return False
    except Exception as e:
        log.exception("database.error", error=str(e))
        return False


def initialize_database():
    """Initialize database tables and schema"""
    log.info("init.initializing_database")
    
    try:
        init_db()
        log.info("database.initialized")
        return True
    except Exception as e:
        log.exception("database.init_failed", error=str(e))
        return False


def check_external_services():
    """Check external service connectivity"""
    log.info("init.checking_external_services")
    
    import asyncio
    import httpx
    from app.config import get_settings
    
    settings = get_settings()
    
    async def _check():
        checks = {
            "ollama": False,
            "chroma": False,
        }
        
        # Check Ollama
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                checks["ollama"] = resp.status_code == 200
        except Exception as e:
            log.warning("service.ollama.unavailable", error=str(e))
        
        # Check Chroma
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(
                    f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v2/tenants/default_tenant"
                )
                checks["chroma"] = resp.status_code == 200
        except Exception as e:
            log.warning("service.chroma.unavailable", error=str(e))
        
        return checks
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(_check())
        loop.close()
        
        log.info("services.check_complete", results=results)
        return results
    except Exception as e:
        log.exception("services.check_failed", error=str(e))
        return {}


def main():
    """Main initialization flow"""
    log.info("=== OmniAgent API Initialization ===")
    
    # Step 1: Validate configuration
    if not validate_config():
        log.error("init.failed.config_invalid")
        return False
    
    # Step 2: Test database connection
    if not test_database():
        log.error("init.failed.database_unreachable")
        log.error("Please ensure PostgreSQL is running and DATABASE_URL is correct")
        return False
    
    # Step 3: Initialize database
    if not initialize_database():
        log.error("init.failed.database_init")
        return False
    
    # Step 4: Check external services (non-critical)
    services = check_external_services()
    if not services.get("ollama"):
        log.warning("init.warning.ollama_unavailable")
    if not services.get("chroma"):
        log.warning("init.warning.chroma_unavailable")
    
    log.info("=== Initialization Complete ===")
    log.info("To start the API, run: uvicorn app.main:app --reload")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
