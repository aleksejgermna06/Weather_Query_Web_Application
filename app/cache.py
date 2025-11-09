import redis
import os
import json
from datetime import timedelta
from typing import Optional
from app.schemas import WeatherData

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

redis_client = redis.from_url(REDIS_URL, decode_responses=False)


def get_cached_weather(key: str) -> Optional[WeatherData]:
    data_bytes = redis_client.get(key)
    if data_bytes:
        try:
            data_str = data_bytes.decode('utf-8')
            d = json.loads(data_str)
            return WeatherData(**d)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as e:
            print(f"Ошибка декодирования кеша Redis для ключа {key}: {e}. Удаляю ключ.")
            redis_client.delete(key)
            return None
    return None


def set_cached_weather(key: str, value: WeatherData, expire_minutes: int = 5):
    data_dict = value.model_dump()

    json_data = json.dumps(data_dict)

    redis_client.setex(key, timedelta(minutes=expire_minutes), json_data)