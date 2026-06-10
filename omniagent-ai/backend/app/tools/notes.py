from typing import Dict, Any
import redis.asyncio as redis
from app.config import get_settings

_r = redis.from_url(get_settings().REDIS_URL, decode_responses=True)


async def notes_tool(args: Dict[str, Any]) -> str:
    action = str(args.get("action", "list"))
    user_id = int(args.get("user_id", 0))
    key = f"notes:{user_id}"
    if action == "add":
        text = str(args.get("text", "")).strip()
        if not text:
            return "No note text."
        await _r.rpush(key, text)
        return f"Added note: {text}"
    if action == "list":
        items = await _r.lrange(key, 0, -1)
        return "\n".join(f"- {x}" for x in items) or "(no notes)"
    if action == "clear":
        await _r.delete(key)
        return "Notes cleared."
    return "Unknown action."