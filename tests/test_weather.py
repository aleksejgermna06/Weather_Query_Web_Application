import pytest
from unittest.mock import AsyncMock, patch
from app.weather import get_weather_for_city
from app.models import WeatherQuery
from app.schemas import WeatherData
from datetime import datetime, timedelta
from app.rate_limiter import is_rate_limited
from app.cache import redis_client
import time


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

    redis_client.expire(f"rate_limit:{ip}", 1)

    time.sleep(1.5)

    assert is_rate_limited(ip) is False


@pytest.mark.asyncio
async def test_cache_hit(test_db):
    city = "Minsk"
    unit = "metric"

    with patch("app.weather.fetch_weather_from_api", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = WeatherData(
            temperature=5.0, description="sunny", humidity=60, wind_speed=2.5
        )

        result1 = await get_weather_for_city(test_db, city, unit, "127.0.0.1")
        assert result1["served_from_cache"] is False
        assert mock_fetch.call_count == 1

        result2 = await get_weather_for_city(test_db, city, unit, "127.0.0.1")
        assert result2["served_from_cache"] is True
        assert mock_fetch.call_count == 1


@pytest.mark.asyncio
async def test_cache_miss_after_expiration(test_db):
    city = "Minsk"
    unit = "metric"

    with patch("app.weather.fetch_weather_from_api", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = WeatherData(
            temperature=5.0, description="sunny", humidity=60, wind_speed=2.5
        )

        await get_weather_for_city(test_db, city, unit, "127.0.0.1")

        redis_client.delete(f"weather:{city.lower()}:{unit}")

        result = await get_weather_for_city(test_db, city, unit, "127.0.0.1")
        assert result["served_from_cache"] is False
        assert mock_fetch.call_count == 2


@pytest.mark.asyncio
async def test_api_failure_returns_500(test_db):
    with patch("app.weather.fetch_weather_from_api", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = Exception("API unreachable")

        with pytest.raises(Exception) as exc_info:
            await get_weather_for_city(test_db, "Minsk", "metric", "127.0.0.1")

        assert "API unreachable" in str(exc_info.value)