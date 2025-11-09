import csv
import tempfile
from app.utils import export_history_to_csv
from app.models import WeatherQuery
from datetime import datetime
import os
import uuid


def test_export_to_csv(test_db):
    unique_city = f"ExportTestCity-{uuid.uuid4().hex[:6]}"

    now = datetime.utcnow()
    query = WeatherQuery(
        city=unique_city,
        unit="metric",
        temperature=5.5,
        description="snow",
        humidity=90,
        wind_speed=4.0,
        served_from_cache=False,
        ip_address="127.0.0.1",
        timestamp=now
    )
    test_db.add(query)
    test_db.commit()

    test_db.add(WeatherQuery(
        city="OtherCity", unit="metric", temperature=0.0,
        description="rain", humidity=80, wind_speed=2.0,
        served_from_cache=False, ip_address="127.0.0.1", timestamp=now
    ))
    test_db.commit()

    file_path = export_history_to_csv(test_db, city=unique_city)

    assert os.path.exists(file_path)
    assert file_path.endswith(".csv")

    with open(file_path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0][1] == "City"
        assert rows[1][1] == unique_city
        assert rows[1][2] == "metric"

    os.remove(file_path)