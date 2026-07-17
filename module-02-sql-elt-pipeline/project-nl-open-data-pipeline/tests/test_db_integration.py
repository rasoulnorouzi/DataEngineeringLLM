"""Integration tests: need the Docker Postgres from docker/docker-compose.yml.

They skip themselves politely when no database is reachable, so `pytest`
stays green on machines without Docker running.
"""

import json

import pytest
from sqlalchemy import create_engine, text

from pipeline import config, load, transform

SAMPLE_RECORDS = [
    {
        "city": "Testville",
        "obs_date": "2026-07-01",
        "payload": json.dumps({"temp_max": 20.0, "temp_min": 10.0, "precip_mm": 0.0}),
    },
    {
        "city": "Testville",
        "obs_date": "2026-07-02",
        "payload": json.dumps({"temp_max": 21.0, "temp_min": 11.0, "precip_mm": 2.5}),
    },
]


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(config.DATABASE_URL)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("No database reachable - start docker compose to run integration tests")
    yield eng
    # Clean up our test city so reruns start fresh.
    with eng.begin() as conn:
        conn.execute(text("DELETE FROM raw.weather_daily WHERE city = 'Testville'"))


def test_upsert_is_idempotent(engine):
    load.ensure_raw_schema(engine)

    load.upsert_raw(engine, SAMPLE_RECORDS)
    load.upsert_raw(engine, SAMPLE_RECORDS)  # the light-switch test: run it twice

    with engine.connect() as conn:
        n = conn.execute(
            text("SELECT count(*) FROM raw.weather_daily WHERE city = 'Testville'")
        ).scalar()
    assert n == 2  # not 4!


def test_transform_builds_staging_and_marts(engine):
    load.ensure_raw_schema(engine)
    load.upsert_raw(engine, SAMPLE_RECORDS)

    executed = transform.run_sql_files(engine)
    assert executed == ["10_staging_weather.sql", "20_marts_weather.sql"]

    with engine.connect() as conn:
        staged = conn.execute(
            text("SELECT count(*) FROM staging.weather_clean WHERE city = 'Testville'")
        ).scalar()
        weekly = conn.execute(
            text("SELECT days_observed FROM marts.weather_weekly WHERE city = 'Testville'")
        ).scalar()
    assert staged == 2
    assert weekly == 2  # both sample days fall in the same ISO week
