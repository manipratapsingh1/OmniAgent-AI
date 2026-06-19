"""
Rate limiting utilities for API protection
"""
from typing import Dict, Tuple
from datetime import datetime, timedelta, timezone
from functools import wraps
import structlog

log = structlog.get_logger("rate_limit")


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str, max_requests: int = 100, window_seconds: int = 60) -> Tuple[bool, Dict]:
        """
        Check if request is allowed under rate limit
        Returns: (is_allowed, info_dict)
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=window_seconds)
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        count = len(self.requests[key])
        is_allowed = count < max_requests
        
        if is_allowed:
            self.requests[key].append(now)
        
        info = {
            "limit": max_requests,
            "remaining": max(0, max_requests - count - (1 if is_allowed else 0)),
            "reset": int((cutoff + timedelta(seconds=window_seconds)).timestamp()),
            "window_seconds": window_seconds
        }
        
        return is_allowed, info


# Global rate limiter instance
_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _limiter


def check_rate_limit(key: str, max_requests: int = 100, window_seconds: int = 60) -> Tuple[bool, Dict]:
    """
    Check rate limit for a given key
    Usage: is_allowed, info = check_rate_limit(user_id, max_requests=100)
    """
    return _limiter.is_allowed(key, max_requests, window_seconds)
