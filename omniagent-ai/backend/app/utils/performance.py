"""
Performance optimization module for chat responses
Includes caching, connection pooling, and async optimizations
"""
import asyncio
import time
import json
import redis
from typing import Any, Dict, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
import structlog
from app.config import get_settings

log = structlog.get_logger("perf_optimizer")
settings = get_settings()


class ResponseCache:
    """Redis-backed response cache for distributed performance"""
    
    def __init__(self, default_ttl: int = 3600):
        self.fallback_cache: Dict[str, tuple[Any, float]] = {}
        try:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis.ping()
            self.enabled = True
            log.info("perf.redis_cache.initialized")
        except Exception as e:
            self.enabled = False
            log.warning("perf.redis_cache.failed_init", error=str(e))
        
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        self.max_size = 10000
        self.cache = self.fallback_cache
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.enabled:
            if key in self.fallback_cache:
                val, exp = self.fallback_cache[key]
                if time.time() < exp:
                    self.hits += 1
                    return val
                del self.fallback_cache[key]
            self.misses += 1
            return None

        try:
            data = self.redis.get(f"resp_cache:{key}")
            if data is not None:
                self.hits += 1
                return json.loads(data)
            self.misses += 1
            return None
        except Exception:
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value"""
        ttl = ttl or self.default_ttl
        
        if not self.enabled:
            self.fallback_cache[key] = (value, time.time() + ttl)
            return

        try:
            self.redis.setex(
                f"resp_cache:{key}",
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            log.error("perf.redis_cache.set_failed", error=str(e))
    
    def clear(self) -> None:
        """Clear cache"""
        if self.enabled:
            try:
                keys = list(self.redis.scan_iter("resp_cache:*"))
                if keys:
                    self.redis.delete(*keys)
            except Exception as e:
                log.warning("perf.redis_cache.clear_failed", error=str(e))
        self.fallback_cache.clear()
        self.cache = self.fallback_cache

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        if self.enabled:
            try:
                size = sum(1 for _ in self.redis.scan_iter("resp_cache:*"))
            except Exception:
                size = 0
        else:
            size = len(self.fallback_cache)
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "size": size,
            "max_size": self.max_size,
        }


class BatchProcessor:
    """Process multiple requests in batches for efficiency"""
    
    def __init__(self, batch_size: int = 10, timeout: float = 0.1):
        self.batch_size = batch_size
        self.timeout = timeout
        self.batch: list = []
        self.futures: list = []
        self.lock = asyncio.Lock()
    
    async def add_item(self, item: Any) -> Any:
        """Add item to batch and get result"""
        future = asyncio.Future()
        
        async with self.lock:
            self.batch.append(item)
            self.futures.append(future)
            
            if len(self.batch) >= self.batch_size:
                await self._process_batch()
        
        # Wait with timeout for batch processing
        try:
            result = await asyncio.wait_for(future, timeout=self.timeout)
            return result
        except asyncio.TimeoutError:
            await self._process_batch()
            return await future
    
    async def _process_batch(self) -> None:
        """Process accumulated batch"""
        if not self.batch:
            return
        
        log.info("batch.process", size=len(self.batch))
        # Batch would be processed here by consuming service
        self.batch.clear()
        self.futures.clear()


class QueryOptimizer:
    """Optimize database queries"""
    
    @staticmethod
    def generate_query_key(*args, **kwargs) -> str:
        """Generate cache key for query results"""
        args_str = ":".join(str(a) for a in args if a is not None)
        kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
        return "|".join(filter(None, [args_str, kwargs_str]))
    
    @staticmethod
    def optimize_context_retrieval(context: list, limit: int = 5) -> list:
        """Optimize context by limiting and prioritizing relevant chunks"""
        if len(context) <= limit:
            return context
        
        # Score by relevance (simplified - could use semantic similarity)
        scored = [(i, chunk) for i, chunk in enumerate(context)]
        # Keep top N most relevant
        return [chunk for _, chunk in sorted(scored, key=lambda x: x[0])[:limit]]


class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    def record(self, metric_name: str, value: float) -> None:
        """Record metric value"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
        
        # Keep last 1000 values
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for metric"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}
        
        values = self.metrics[metric_name]
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values),
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get all metrics"""
        return {name: self.get_stats(name) for name in self.metrics}


# Global instances
_response_cache = ResponseCache()
_query_optimizer = QueryOptimizer()
_perf_monitor = PerformanceMonitor()


def get_response_cache() -> ResponseCache:
    """Get global response cache"""
    return _response_cache


def get_query_optimizer() -> QueryOptimizer:
    """Get query optimizer"""
    return _query_optimizer


def get_perf_monitor() -> PerformanceMonitor:
    """Get performance monitor"""
    return _perf_monitor


def measure_time(metric_name: str):
    """Decorator to measure and record execution time"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = (time.time() - start) * 1000  # Convert to ms
                _perf_monitor.record(metric_name, elapsed)
                log.debug("perf.measure", metric=metric_name, elapsed_ms=round(elapsed, 2))
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = (time.time() - start) * 1000  # Convert to ms
                _perf_monitor.record(metric_name, elapsed)
                log.debug("perf.measure", metric=metric_name, elapsed_ms=round(elapsed, 2))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
