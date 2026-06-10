#!/usr/bin/env python3
"""
Production-ready startup script for OmniAgent API
Configures uvicorn with proper timeout settings for large file uploads
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from app.main import create_app
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    # Create the app
    app = create_app()
    
    # Configure uvicorn with appropriate timeouts and settings
    # timeout_keep_alive: keep connection alive for extended periods
    # This allows long-running file uploads, database queries, and processing
    uvicorn.run(
        app,
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        log_level="info",
        # Timeout settings for large file uploads and slow connections
        timeout_keep_alive=300,  # Increased from 120 to 300 seconds (5 minutes)
        # Connection pool settings
        limit_concurrency=100,
        limit_max_requests=10000,
        # Access log configuration
        access_log=True,
    )
