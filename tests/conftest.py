import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.database import Base, get_db
from app.main import app
import os
import time

TEST_DATABASE_URL = os.getenv("DATABASE_URL")

MAX_RETRIES = 10
RETRY_DELAY = 1

engine = None
TestingSessionLocal = None

for attempt in range(MAX_RETRIES):
    try:
        engine = create_engine(
            TEST_DATABASE_URL,
            poolclass=NullPool
        )
        with engine.connect() as connection:
            connection.close()
        print(f"Database connection successful after {attempt + 1} attempt(s).")

        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        break

    except Exception as e:
        if attempt == MAX_RETRIES - 1:
            print(f"Failed to connect to database after {MAX_RETRIES} attempts.")
            raise e
        print(f"Database connection failed on attempt {attempt + 1}/{MAX_RETRIES}. Retrying in {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    if engine is None:
        raise Exception("SQLAlchemy Engine failed to initialize globally.")

    print("Creating database schema...")
    Base.metadata.create_all(bind=engine)

    yield

    print("Dropping database schema...")
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db():
    connection = engine.connect()
    transaction = connection.begin()

    db = TestingSessionLocal(bind=connection)

    try:
        yield db
    finally:
        transaction.rollback()
        db.close()
        connection.close()


@pytest.fixture
def test_client():
    def override_get_db():
        connection = engine.connect()
        transaction = connection.begin()
        db = TestingSessionLocal(bind=connection)

        try:
            yield db
        finally:
            transaction.rollback()
            db.close()
            connection.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()