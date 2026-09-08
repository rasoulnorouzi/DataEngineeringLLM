"""Weather endpoints - unit tests, no database.

Every test here runs against the cardboard prep station from conftest.py.
They prove CONTRACTS: status codes, shapes, validation, error paths.
They do NOT prove the SQL is correct - that is test_db_integration.py's job.
"""

import pytest

# --------------------------------------------------------------------------
# happy paths
# --------------------------------------------------------------------------

def test_list_cities_returns_a_list(client):
    r = client.get("/weather/cities")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert body[0]["city"] == "Amsterdam"
    assert body[0]["days_observed"] == 1


def test_daily_returns_rows(client):
    r = client.get("/weather/daily")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_daily_filters_by_city(client):
    r = client.get("/weather/daily", params={"city": "Utrecht"})
    assert r.status_code == 200
    assert {row["city"] for row in r.json()} == {"Utrecht"}


def test_weekly_returns_the_mart(client):
    r = client.get("/weather/weekly", params={"city": "Utrecht"})
    assert r.status_code == 200
    row = r.json()[0]
    assert row["week_start"] == "2026-08-31"
    assert row["temp_change_vs_prev_week_c"] == pytest.approx(-1.3)


def test_city_stats(client):
    r = client.get("/weather/cities/Utrecht/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["days_observed"] == 2
    assert body["warmest_temp_c"] == pytest.approx(21.4)


# --------------------------------------------------------------------------
# the response model is an ALLOW-LIST: undeclared fields cannot leak
# --------------------------------------------------------------------------

def test_daily_response_shape_is_exactly_the_contract(client):
    """Here exact equality is right: the complete key set IS the promise."""
    row = client.get("/weather/daily").json()[0]
    assert set(row) == {"city", "obs_date", "temp_max_c", "temp_min_c", "precip_mm"}


# --------------------------------------------------------------------------
# unhappy paths - the ones people forget to write
# --------------------------------------------------------------------------

def test_unknown_city_stats_is_404(client):
    r = client.get("/weather/cities/Atlantis/stats")
    assert r.status_code == 404
    assert "Atlantis" in r.json()["detail"]


def test_bad_sort_column_is_422_not_500(client):
    """An invalid sort key is the CALLER's mistake, so 4xx - and it must never
    reach the SQL string."""
    r = client.get("/weather/daily", params={"sort_by": "; DROP TABLE staging.weather_clean;--"})
    assert r.status_code == 422
    assert "sort_by" in r.json()["detail"]


def test_bad_direction_is_422(client):
    r = client.get("/weather/daily", params={"direction": "sideways"})
    assert r.status_code == 422


def test_reversed_date_range_is_422(client):
    r = client.get("/weather/daily", params={"from_date": "2026-09-10", "to_date": "2026-09-01"})
    assert r.status_code == 422


def test_bad_date_format_is_422_naming_the_field(client):
    """422 alone isn't enough - check the error points at the RIGHT field."""
    r = client.get("/weather/daily", params={"from_date": "not-a-date"})
    assert r.status_code == 422
    locations = [tuple(e["loc"]) for e in r.json()["detail"]]
    assert ("query", "from_date") in locations


@pytest.mark.parametrize(
    ("params", "expected_status"),
    [
        ({"limit": 0}, 422),        # ge=1
        ({"limit": -5}, 422),       # ge=1
        ({"offset": -1}, 422),      # ge=0
        ({"limit": 100_000}, 422),  # above max_page_size
        ({"limit": 1}, 200),        # the boundary that must WORK
        ({"offset": 0}, 200),
    ],
)
def test_pagination_bounds(client, params, expected_status):
    assert client.get("/weather/daily", params=params).status_code == expected_status


def test_limit_and_offset_reach_the_query_as_bind_parameters(client):
    """The fake applies :limit and :offset, so the row count proves they arrived."""
    assert len(client.get("/weather/daily", params={"limit": 2}).json()) == 2
    assert len(client.get("/weather/daily", params={"offset": 2}).json()) == 1
    assert client.get("/weather/daily", params={"offset": 99}).json() == []


# --------------------------------------------------------------------------
# SQL injection: values must never become syntax
# --------------------------------------------------------------------------

def test_city_filter_is_bound_not_interpolated(client):
    """A malicious city name is data, not SQL. It simply matches nothing."""
    r = client.get("/weather/daily", params={"city": "'; DROP SCHEMA staging CASCADE;--"})
    assert r.status_code == 200
    assert r.json() == []
