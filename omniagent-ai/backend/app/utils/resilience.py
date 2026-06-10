import time
import asyncio
import structlog
from typing import Callable, Any, Optional
from enum import Enum

log = structlog.get_logger("resilience")

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """God-level resilience: Prevents cascading failures in external services."""
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: Optional[float] = None

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                log.info("circuit.half_open", service=self.name)
                self.state = CircuitState.HALF_OPEN
            else:
                log.warning("circuit.open.blocked", service=self.name)
                raise Exception(f"Circuit Breaker [{self.name}] is OPEN. Service unavailable.")

        try:
            start_time = time.time()
            result = await func(*args, **kwargs)
            
            # If successful and was half-open or closed, reset
            if self.state == CircuitState.HALF_OPEN:
                log.info("circuit.closed", service=self.name)
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                log.error("circuit.opened", service=self.name, error=str(e), threshold=self.failure_threshold)
                self.state = CircuitState.OPEN
            
            raise e

# Global Registry
breakers = {
    "ollama": CircuitBreaker("ollama", failure_threshold=3, recovery_timeout=60),
    "redis": CircuitBreaker("redis", failure_threshold=5, recovery_timeout=30),
    "chroma": CircuitBreaker("chroma", failure_threshold=3, recovery_timeout=45),
}
