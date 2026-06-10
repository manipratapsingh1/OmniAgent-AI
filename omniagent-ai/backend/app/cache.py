import json
import hashlib
from typing import Any, Optional
from redis import Redis
from app.config import get_settings

_settings = get_settings()


def _get_redis() -> Redis:
    return Redis.from_url(_settings.REDIS_URL)


def key_for_text(prefix: str, model: str, text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8", errors="ignore"))
    return f"{prefix}:{model}:{h.hexdigest()}"


def get_json(key: str) -> Optional[Any]:
    r = _get_redis()
    try:
        val = r.get(key)
        if not val:
            return None
        return json.loads(val)
    except Exception:
        return None


def set_json(key: str, value: Any, ex: int = 3600) -> bool:
    r = _get_redis()
    try:
        r.set(key, json.dumps(value), ex=ex)
        return True
    except Exception:
        return False
