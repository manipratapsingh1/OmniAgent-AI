from typing import List
import redis.asyncio as redis
from app.config import get_settings

_r = redis.from_url(get_settings().REDIS_URL, decode_responses=True)


async def append(conversation_id: int, role: str, content: str) -> None:
    key = f"conv:{conversation_id}:recent"
    await _r.rpush(key, f"{role}: {content[:1000]}")
    await _r.ltrim(key, -20, -1)
    await _r.expire(key, 60 * 60 * 24)


async def get_recent(conversation_id: int, limit: int = 6) -> List[str]:
    key = f"conv:{conversation_id}:recent"
    items = await _r.lrange(key, -limit, -1)
    return items or []