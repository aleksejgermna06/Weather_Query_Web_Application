import csv
import tempfile
import os
from sqlalchemy.orm import Session
from app.models import WeatherQuery
from datetime import datetime


def export_history_to_csv(
        db: Session,
        city: str = None,
        date_from: datetime = None,
        date_to: datetime = None
) -> str:
    query = db.query(WeatherQuery)

    if city:
        query = query.filter(WeatherQuery.city.ilike(f"%{city}%"))
    if date_from:
        query = query.filter(WeatherQuery.timestamp >= date_from)
    if date_to:
        query = query.filter(WeatherQuery.timestamp <= date_to)

    results = query.all()

    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "weather_history.csv")

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "City", "Unit", "Temperature", "Description",
            "Humidity (%)", "Wind Speed", "Served from Cache",
            "IP Address", "Timestamp"
        ])
        for r in results:
            writer.writerow([
                r.id,
                r.city,
                r.unit,
                r.temperature,
                r.description,
                r.humidity,
                r.wind_speed,
                "Yes" if r.served_from_cache else "No",
                r.ip_address,
                r.timestamp.isoformat()
            ])
    return file_path