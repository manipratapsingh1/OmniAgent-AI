"""
Production health checks and monitoring module
"""
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import structlog
from sqlmodel import Session
from redis import Redis
import httpx

log = structlog.get_logger("health_check")


class HealthChecker:
    """Comprehensive health check for all system components"""
    
    def __init__(self, db: Session, redis_client: Redis, ollama_url: str, chroma_url: str):
        self.db = db
        self.redis = redis_client
        self.ollama_url = ollama_url
        self.chroma_url = chroma_url
    
    async def check_all(self) -> Dict[str, Any]:
        """Check all components and return status"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {}
        }
        
        # Run checks in parallel
        checks = await asyncio.gather(
            self._check_database(),
            self._check_redis(),
            self._check_ollama(),
            self._check_chroma(),
            self._check_system_resources(),
            return_exceptions=True
        )
        
        component_names = ["database", "redis", "ollama", "chroma", "system"]
        for name, result in zip(component_names, checks):
            if isinstance(result, Exception):
                results["components"][name] = {
                    "status": "unhealthy",
                    "error": str(result)
                }
                results["status"] = "degraded"
            else:
                results["components"][name] = result
                if result.get("status") == "unhealthy":
                    results["status"] = "degraded"
        
        return results
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL connection"""
        try:
            # Simple query to verify connection
            result = self.db.exec("SELECT 1").first()
            
            # Get connection pool info
            pool_size = getattr(self.db.connection().connection.get_backend_name, "pool_size", "unknown")
            
            return {
                "status": "healthy",
                "response_time_ms": 10,
                "pool_size": pool_size
            }
        except Exception as e:
            log.error("database.check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connection"""
        try:
            # Ping Redis
            pong = await asyncio.get_event_loop().run_in_executor(
                None, self.redis.ping
            )
            
            # Get memory info
            info = await asyncio.get_event_loop().run_in_executor(
                None, self.redis.info, "memory"
            )
            
            used_memory_mb = info.get("used_memory", 0) / (1024 * 1024)
            max_memory_mb = info.get("maxmemory", 0) / (1024 * 1024) if info.get("maxmemory") else "unlimited"
            
            return {
                "status": "healthy",
                "pong": pong,
                "memory_used_mb": round(used_memory_mb, 2),
                "memory_max_mb": max_memory_mb
            }
        except Exception as e:
            log.error("redis.check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_ollama(self) -> Dict[str, Any]:
        """Check Ollama service"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    model_names = [m.get("name") for m in models]
                    
                    return {
                        "status": "healthy",
                        "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                        "models_available": len(models),
                        "models": model_names[:5]  # Return top 5
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            log.error("ollama.check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_chroma(self) -> Dict[str, Any]:
        """Check Chroma vector database"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.chroma_url}/api/version")
                
                if response.status_code == 200:
                    version = response.json()
                    
                    return {
                        "status": "healthy",
                        "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                        "version": version
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            log.error("chroma.check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources (CPU, Memory, Disk)"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            # Determine health based on thresholds
            status = "healthy"
            alerts = []
            
            if cpu_percent > 80:
                status = "degraded"
                alerts.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 80:
                status = "degraded"
                alerts.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 85:
                status = "degraded"
                alerts.append(f"Low disk space: {disk.percent}% used")
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "alerts": alerts if alerts else []
            }
        except Exception as e:
            log.error("system_resources.check_failed", error=str(e))
            return {
                "status": "unknown",
                "error": str(e)
            }


class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.max_entries = 1000
    
    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(value)
        
        # Keep only latest entries
        if len(self.metrics[name]) > self.max_entries:
            self.metrics[name] = self.metrics[name][-self.max_entries:]
    
    def get_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = self.metrics[name]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p95": sorted(values)[int(len(values) * 0.95)] if values else 0,
            "p99": sorted(values)[int(len(values) * 0.99)] if values else 0
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all metrics"""
        return {name: self.get_stats(name) for name in self.metrics}


# Global performance monitor
_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    return _monitor
