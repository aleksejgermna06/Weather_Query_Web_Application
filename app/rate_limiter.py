import redis
import os
from datetime import datetime, timedelta

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL)


def is_rate_limited(ip: str, max_req: int = 30, window: int = 60) -> bool:
    key = f"rate_limit:{ip}"
    current = redis_client.get(key)

    if current is None:
        redis_client.setex(key, window, 1)
        return False
    elif int(current) < max_req:
        redis_client.incr(key)
        return False
    else:
        return True