import pytest
from app.rate_limiter import is_rate_limited
from app.cache import redis_client

@pytest.fixture(autouse=True)
def clear_redis():
    redis_client.flushall()

@pytest.mark.asyncio
async def test_rate_limit_allows_30_requests():
    ip = "192.168.1.1"

    for _ in range(30):
        assert is_rate_limited(ip) is False

    assert is_rate_limited(ip) is True

@pytest.mark.asyncio
async def test_rate_limit_resets_after_60_seconds():
    ip = "192.168.1.1"

    for _ in range(30):
        assert is_rate_limited(ip) is False

    from app.rate_limiter import redis_client
    redis_client.expire(f"rate_limit:{ip}", 1)

    import time
    time.sleep(2)

    assert is_rate_limited(ip) is False