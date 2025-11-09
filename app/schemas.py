from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WeatherData(BaseModel):
    temperature: float
    description: str
    humidity: int
    wind_speed: float

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    description: str
    unit: str
    timestamp: datetime
    served_from_cache: bool

class QueryHistoryResponse(BaseModel):
    id: int
    city: str
    unit: str
    temperature: float
    description: str
    humidity: int
    wind_speed: float
    served_from_cache: bool
    timestamp: datetime
    ip_address: str

    class Config:
        from_attributes = True