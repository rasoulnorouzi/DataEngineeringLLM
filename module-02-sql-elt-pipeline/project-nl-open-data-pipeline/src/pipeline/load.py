"""Load step: idempotent upsert into the raw layer."""

import logging

from sqlalchemy import Engine, text

logger = logging.getLogger(__name__)

CREATE_RAW = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.weather_daily (
    city        TEXT        NOT NULL,
    obs_date    DATE        NOT NULL,
    payload     JSONB       NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT weather_daily_pk PRIMARY KEY (city, obs_date)
);
"""

# The "light switch": rerunning with the same (city, obs_date) overwrites
# instead of duplicating. See Day 6 theory - idempotency.
UPSERT = text("""
    INSERT INTO raw.weather_daily (city, obs_date, payload)
    VALUES (:city, :obs_date, CAST(:payload AS JSONB))
    ON CONFLICT (city, obs_date)
    DO UPDATE SET payload = EXCLUDED.payload,
                  loaded_at = now()
""")


def ensure_raw_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql(CREATE_RAW)


def upsert_raw(engine: Engine, records: list[dict]) -> int:
    """Upsert records into raw.weather_daily. Returns the number of records sent."""
    if not records:
        logger.warning("No records to load")
        return 0
    with engine.begin() as conn:
        conn.execute(UPSERT, records)
    logger.info("Upserted %d records into raw.weather_daily", len(records))
    return len(records)
