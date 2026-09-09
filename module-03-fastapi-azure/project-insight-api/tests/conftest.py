"""Shared fixtures.

The important one is `client`: it swaps the real database connection for a fake
via app.dependency_overrides, so the unit tests need no Postgres at all.

That swap is only possible because every handler ASKS for its connection with
Depends(get_conn) instead of building one itself. (Day 4 -> Day 5)
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from insight_api.deps import get_conn
from insight_api.main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def rows() -> dict:
    """Canned, real-shaped data. Never call a real database in a unit test."""
    return json.loads((FIXTURES / "weather_rows.json").read_text(encoding="utf-8"))


class FakeResult:
    """Stands in for the object SQLAlchemy's .execute() returns."""

    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> list[dict]:
        return self._records

    def first(self) -> dict | None:
        return self._records[0] if self._records else None

    def scalar(self):
        if not self._records:
            return None
        return next(iter(self._records[0].values()))


class FakeConnection:
    """A connection that answers from a script instead of a database.

    `router` receives the SQL text and the parameters, and decides what to
    return - which lets one fake serve every endpoint.
    """

    def __init__(self, router) -> None:
        self._router = router
        self.executed: list[tuple[str, dict]] = []

    def execute(self, statement, params: dict | None = None) -> FakeResult:
        sql = str(statement)
        self.executed.append((sql, params or {}))
        return FakeResult(self._router(sql, params or {}))


@pytest.fixture
def fake_router(rows):
    """Route SQL to canned rows by looking at which table it mentions."""

    def route(sql: str, params: dict) -> list[dict]:
        if "SELECT 1" in sql:
            return [{"?column?": 1}]
        if "marts.weather_weekly" in sql:
            data = rows["weekly"]
        elif "GROUP BY city" in sql and "min(obs_date)" in sql:
            data = rows["cities"]
        elif "WITH base AS" in sql:
            city = params.get("city")
            days = [r for r in rows["daily"] if r["city"] == city]
            if not days:
                return [{"city": city, "days_observed": 0, "first_observation": None,
                         "last_observation": None, "warmest_day": None, "warmest_temp_c": None,
                         "coldest_day": None, "coldest_temp_c": None, "total_precip_mm": None}]
            return [{
                "city": city,
                "days_observed": len(days),
                "first_observation": min(r["obs_date"] for r in days),
                "last_observation": max(r["obs_date"] for r in days),
                "warmest_day": max(days, key=lambda r: r["temp_max_c"])["obs_date"],
                "warmest_temp_c": max(r["temp_max_c"] for r in days),
                "coldest_day": min(days, key=lambda r: r["temp_min_c"])["obs_date"],
                "coldest_temp_c": min(r["temp_min_c"] for r in days),
                "total_precip_mm": round(sum(r["precip_mm"] for r in days), 1),
            }]
        else:
            data = rows["daily"]

        city = params.get("city")
        if city is not None:
            data = [r for r in data if r["city"] == city]

        # Honour the paging bind parameters, so tests can assert they arrived.
        offset = params.get("offset", 0)
        limit = params.get("limit")
        data = data[offset:]
        if limit is not None:
            data = data[:limit]
        return data

    return route


@pytest.fixture
def client(fake_router):
    """A TestClient whose database is made of cardboard."""

    def override_get_conn():
        yield FakeConnection(fake_router)

    app.dependency_overrides[get_conn] = override_get_conn
    yield TestClient(app)
    app.dependency_overrides.clear()      # teardown: never leak into another test


@pytest.fixture
def broken_db_client():
    """A TestClient whose database refuses every query - for the 503 path."""

    class DeadConnection:
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("connection refused")

    def override_get_conn():
        yield DeadConnection()

    app.dependency_overrides[get_conn] = override_get_conn
    yield TestClient(app)
    app.dependency_overrides.clear()
