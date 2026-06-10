"""Background job queue (Redis + RQ).
Scaffolded — used for async heavy ingestion / long jobs."""
from redis import Redis
from rq import Queue
from app.config import get_settings

_settings = get_settings()
redis_conn = Redis.from_url(_settings.REDIS_URL)
default_queue = Queue("omniagent", connection=redis_conn)