from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import logging
import time
import os
from app.database import SessionLocal, engine
from app.models import Base
from app.weather import get_weather_for_city
from app.rate_limiter import is_rate_limited
from app.utils import export_history_to_csv
from app.schemas import WeatherResponse, QueryHistoryResponse
from datetime import datetime
from sqlalchemy import text
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application")
    yield
    logger.info("Shutting down application")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"request start path={request.url.path} method={request.method}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"request end path={request.url.path} method={request.method} status={response.status_code} duration={process_time:.3f}s")
    return response


@app.get("/weather")
async def weather_endpoint(
        city: str,
        unit: str = Query("metric", regex="^(metric|imperial)$"),
        request: Request = None,
        db: Session = Depends(get_db)
):
    client_ip = request.client.host

    if is_rate_limited(client_ip):
        logger.warning(f"rate_limit_exceeded ip={client_ip}")
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")

    try:
        result = await get_weather_for_city(db, city, unit, client_ip)
        return WeatherResponse(**result)
    except Exception as e:
        logger.error(f"weather_fetch_error city={city} error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch weather data")


@app.get("/history", response_model=list[QueryHistoryResponse])
async def get_history(
        city: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        page: int = 1,
        page_size: int = 10,
        db: Session = Depends(get_db)
):
    from app.weather import get_query_history
    return get_query_history(db, city, date_from, date_to, page, page_size)


@app.get("/export")
async def export_history(
        city: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        db: Session = Depends(get_db)
):
    file_path = export_history_to_csv(db, city, date_from, date_to)
    return FileResponse(file_path, media_type='text/csv', filename='weather_history.csv')


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1"))
        db.commit()
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"status": "unhealthy", "db": "down", "error": str(e)})

    import httpx
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("https://api.openweathermap.org/data/2.5/weather?q=London&appid=dummy")
            api_ok = resp.status_code != 401
    except Exception:
        api_ok = False

    status = "healthy" if api_ok else "degraded"
    return {"status": status, "db": "up", "api_reachable": api_ok}