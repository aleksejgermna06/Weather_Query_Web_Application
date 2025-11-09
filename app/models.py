from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class WeatherQuery(Base):
    __tablename__ = "weather_queries"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    unit = Column(String)
    temperature = Column(Float)
    description = Column(String)
    humidity = Column(Integer)
    wind_speed = Column(Float)
    served_from_cache = Column(Boolean, default=False)
    ip_address = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)