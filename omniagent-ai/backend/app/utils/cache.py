"""
Caching utilities for improving performance
"""
from typing import Any, Optional, Callable
from datetime import datetime, timedelta, timezone
from functools import wraps
import json
import structlog

log = structlog.get_logger("cache")


class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self.data: dict = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self.data:
            return None
        
        value, expiry = self.data[key]
        if datetime.now(timezone.utc) > expiry:
            del self.data[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL"""
        expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self.data[key] = (value, expiry)
        log.debug("cache.set", key=key, ttl=ttl_seconds)
    
    def delete(self, key: str) -> None:
        """Delete value from cache"""
        if key in self.data:
            del self.data[key]
            log.debug("cache.delete", key=key)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.data.clear()
        log.info("cache.cleared")


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get global cache instance"""
    return _cache


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from prefix and arguments"""
    args_str = ":".join(str(a) for a in args)
    kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    parts = [prefix, args_str, kwargs_str]
    return ":".join(p for p in parts if p)


def cached(ttl_seconds: int = 300, key_prefix: str = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            prefix = key_prefix or func.__name__
            key = cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            result = _cache.get(key)
            if result is not None:
                log.debug("cache.hit", key=key)
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl_seconds)
            log.debug("cache.miss", key=key)
            return result
        
        return wrapper
    return decorator
