"""Integration tests: these need the real Module 2 database.

They skip themselves politely when no database is reachable, so `pytest` stays
green on a machine with Docker stopped.

REMEMBER: `12 passed, 5 skipped` is NOT `17 passed`. If these skip, your SQL was
never executed. The CI workflow runs them against a real Postgres service
container so that they cannot be silently skipped forever.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from insight_api.config import get_settings
from insight_api.main import app


@pytest.fixture(scope="module")
def live_client():
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.execute(text("SELECT 1 FROM staging.weather_clean LIMIT 1"))
    except Exception:
        pytest.skip(
            "No database with staging.weather_clean reachable - start the Module 2 stack "
            "and run `python -m pipeline.run` first"
        )
    engine.dispose()
    with TestClient(app) as client:      # `with` runs lifespan: the engine is created
        yield client


def test_readiness_against_real_database(live_client):
    r = live_client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"


def test_cities_endpoint_runs_real_sql(live_client):
    r = live_client.get("/weather/cities")
    assert r.status_code == 200
    body = r.json()
    assert len(body) > 0
    assert all("city" in row and "days_observed" in row for row in body)


def test_daily_endpoint_runs_real_sql(live_client):
    r = live_client.get("/weather/daily", params={"limit": 5})
    assert r.status_code == 200
    assert len(r.json()) <= 5


def test_daily_sorting_actually_sorts(live_client):
    """Proves the ORDER BY allow-list produces real, valid SQL."""
    r = live_client.get(
        "/weather/daily", params={"sort_by": "date", "direction": "asc", "limit": 5}
    )
    assert r.status_code == 200
    dates = [row["obs_date"] for row in r.json()]
    assert dates == sorted(dates)


def test_weekly_endpoint_reads_the_mart(live_client):
    r = live_client.get("/weather/weekly", params={"limit": 3})
    assert r.status_code == 200
    for row in r.json():
        assert "avg_temp_max_c" in row


def test_decimal_columns_serialise_as_numbers(live_client):
    """Postgres NUMERIC arrives as Decimal, which json cannot serialise.

    This passes only because the response models declare float. Without them
    this endpoint would 500 in production while every unit test stayed green.
    """
    rows = live_client.get("/weather/daily", params={"limit": 1}).json()
    if rows and rows[0]["temp_max_c"] is not None:
        assert isinstance(rows[0]["temp_max_c"], (int, float))
