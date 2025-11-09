from sqlalchemy.orm import Session
from app.models import WeatherQuery
from app.cache import get_cached_weather, set_cached_weather
from app.schemas import WeatherData
import httpx
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


async def fetch_weather_from_api(city: str, unit: str) -> WeatherData:
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": unit
    }
    async with httpx.AsyncClient() as client:
        start = datetime.utcnow().timestamp()
        resp = await client.get(OPENWEATHER_URL, params=params)
        latency = datetime.utcnow().timestamp() - start
        logger.info(f"external_api_latency api=openweathermap latency={latency:.3f}s city={city}")

        if resp.status_code != 200:
            raise Exception(f"API error: {resp.text}")

        data = resp.json()
        return WeatherData(
            temperature=data["main"]["temp"],
            description=data["weather"][0]["description"],
            humidity=data["main"]["humidity"],
            wind_speed=data["wind"]["speed"]
        )


async def get_weather_for_city(db: Session, city: str, unit: str, ip: str):
    cache_key = f"weather:{city.lower()}:{unit}"
    cached = get_cached_weather(cache_key)
    served_from_cache = False

    if cached:
        weather_data = cached
        served_from_cache = True
        logger.info(f"cache_hit city={city} unit={unit}")
    else:
        weather_data = await fetch_weather_from_api(city, unit)
        set_cached_weather(cache_key, weather_data)
        logger.info(f"cache_miss city={city} unit={unit}")

    query = WeatherQuery(
        city=city,
        unit=unit,
        temperature=weather_data.temperature,
        description=weather_data.description,
        humidity=weather_data.humidity,
        wind_speed=weather_data.wind_speed,
        served_from_cache=served_from_cache,
        ip_address=ip
    )
    db.add(query)
    db.commit()
    db.refresh(query)

    return {
        "city": city,
        "temperature": weather_data.temperature,
        "description": weather_data.description,
        "unit": unit,
        "timestamp": query.timestamp,
        "served_from_cache": served_from_cache
    }


def get_query_history(db: Session, city: str = None, date_from: datetime = None,
                      date_to: datetime = None, page: int = 1, page_size: int = 10):
    query = db.query(WeatherQuery)

    if city:
        query = query.filter(WeatherQuery.city.ilike(f"%{city}%"))
    if date_from:
        query = query.filter(WeatherQuery.timestamp >= date_from)
    if date_to:
        query = query.filter(WeatherQuery.timestamp <= date_to)

    total = query.count()
    items = query.order_by(WeatherQuery.timestamp.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    return items