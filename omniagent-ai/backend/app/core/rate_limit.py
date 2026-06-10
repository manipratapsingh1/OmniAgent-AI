import redis.asyncio as redis
from fastapi import HTTPException

from app.config import get_settings

_settings = get_settings()
_redis = redis.from_url(_settings.REDIS_URL, decode_responses=True)


async def enforce_rate_limit(key: str) -> None:
    bucket = f"rl:{key}"
    try:
        count = await _redis.incr(bucket)
        if count == 1:
            await _redis.expire(bucket, 60)
        if count > _settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except redis.RedisError:
        # Fail-open if Redis is down; logged elsewhere.
        return