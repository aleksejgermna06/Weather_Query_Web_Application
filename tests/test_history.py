import pytest
from datetime import datetime, timedelta
from app.weather import get_query_history
from app.models import WeatherQuery
import uuid


def test_get_history_pagination(test_db):
    unique_prefix = f"PageTest-{uuid.uuid4().hex[:4]}"
    now = datetime.utcnow()

    for i in range(15):
        query = WeatherQuery(
            city=f"{unique_prefix}-City",
            unit="metric",
            temperature=20.0,
            description="clear",
            humidity=50,
            wind_speed=3.0,
            served_from_cache=False,
            ip_address="127.0.0.1",
            timestamp=now - timedelta(minutes=i)
        )
        test_db.add(query)
    test_db.commit()

    page1 = get_query_history(test_db, page=1, page_size=10, city=f"{unique_prefix}-City")
    assert len(page1) == 10

    page2 = get_query_history(test_db, page=2, page_size=10, city=f"{unique_prefix}-City")
    assert len(page2) == 5


def test_filter_by_city(test_db):
    unique_city_base = f"FilterCity-{uuid.uuid4().hex[:4]}"
    now = datetime.utcnow()

    cities_to_find = [unique_city_base.upper(), unique_city_base.lower(), unique_city_base.capitalize()]

    for city in cities_to_find + ["OtherCity"]:
        query = WeatherQuery(
            city=city,
            unit="metric",
            temperature=20.0,
            description="clear",
            humidity=50,
            wind_speed=3.0,
            served_from_cache=False,
            ip_address="127.0.0.1",
            timestamp=now
        )
        test_db.add(query)
    test_db.commit()

    results = get_query_history(test_db, city=unique_city_base)
    assert len(results) == 3


def test_filter_by_date_range(test_db):
    unique_prefix = f"DateTest-{uuid.uuid4().hex[:4]}"
    now = datetime.utcnow()

    old = now - timedelta(days=2)
    recent = now - timedelta(hours=1)

    for i, ts in enumerate([old, recent, recent]):
        query = WeatherQuery(
            city=f"{unique_prefix}-City{i}",
            unit="metric",
            temperature=20.0,
            description="clear",
            humidity=50,
            wind_speed=3.0,
            served_from_cache=False,
            ip_address="127.0.0.1",
            timestamp=ts
        )
        test_db.add(query)
    test_db.commit()

    results = get_query_history(
        test_db,
        city=unique_prefix,
        date_from=now - timedelta(hours=2)
    )
    assert len(results) == 2

    results_all = get_query_history(
        test_db,
        city=unique_prefix,
        date_from=now - timedelta(days=3)
    )
    assert len(results_all) == 3