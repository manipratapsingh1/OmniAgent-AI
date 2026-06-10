import os
from rq import Queue
from redis import Redis
from rq.worker import Worker, SimpleWorker

from app.config import get_settings


def main():
    settings = get_settings()
    conn = Redis.from_url(settings.REDIS_URL)
    print("Connecting to", conn)
    q = Queue('omniagent', connection=conn)
    try:
        print("Queue size:", q.count)
    except Exception:
        print("Could not read queue size")
    # On Windows, Worker uses os.fork which is unsupported; use SimpleWorker instead
    if os.name == "nt":
        w = SimpleWorker([q], connection=conn)
    else:
        w = Worker([q], connection=conn)
    print("Starting worker; press Ctrl+C to stop")
    w.work()


if __name__ == "__main__":
    main()
