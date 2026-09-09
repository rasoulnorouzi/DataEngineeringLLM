"""Weather endpoints - the actual product.

Reads the Module 2 warehouse:
    staging.weather_clean   typed daily rows      -> /weather/daily
    marts.weather_weekly    weekly aggregates     -> /weather/weekly

It never reads `raw`. Raw is the evidence locker: JSONB in whatever shape the
source sent it. An API that reads raw re-implements the staging SQL in Python
and then drifts away from it.

Every value a caller supplies travels as a BIND PARAMETER (:city). Identifiers
cannot be bound, so the sort column comes from an allow-list we control.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Connection, text

from insight_api.deps import Pagination, get_conn, pagination
from insight_api.models import CityOut, CityStatsOut, DailyObservationOut, WeeklySummaryOut

router = APIRouter(prefix="/weather", tags=["weather"])

# Caller-facing key -> real column name. The caller never supplies a column
# name; they supply a KEY, and we supply the column. (Day 4)
SORTABLE_DAILY = {
    "date": "obs_date",
    "temp_max": "temp_max_c",
    "temp_min": "temp_min_c",
    "precip": "precip_mm",
}
DIRECTIONS = {"asc": "ASC", "desc": "DESC"}


@router.get("/cities", response_model=list[CityOut], summary="Cities with data")
def list_cities(conn: Connection = Depends(get_conn)) -> list:
    """Which cities can I ask about, and what period do they cover?"""
    return conn.execute(
        text("""
            SELECT
                city,
                min(obs_date) AS first_observation,
                max(obs_date) AS last_observation,
                count(*)      AS days_observed
            FROM staging.weather_clean
            GROUP BY city
            ORDER BY city
        """)
    ).mappings().all()


@router.get("/daily", response_model=list[DailyObservationOut], summary="Daily observations")
def read_daily(
    city: str | None = Query(default=None, description="Filter to one city"),
    from_date: date | None = Query(default=None, description="Inclusive start date"),
    to_date: date | None = Query(default=None, description="Inclusive end date"),
    sort_by: str = Query(default="date", description=f"One of: {', '.join(SORTABLE_DAILY)}"),
    direction: str = Query(default="desc", description="asc or desc"),
    page: Pagination = Depends(pagination),
    conn: Connection = Depends(get_conn),
) -> list:
    """Daily rows from the staging layer, filtered and paged."""
    column = SORTABLE_DAILY.get(sort_by)
    if column is None:
        raise HTTPException(
            status_code=422,
            detail=f"sort_by must be one of {sorted(SORTABLE_DAILY)}",
        )
    direction_sql = DIRECTIONS.get(direction)
    if direction_sql is None:
        raise HTTPException(status_code=422, detail="direction must be 'asc' or 'desc'")

    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date must not be after to_date")

    # Build the WHERE clause from the filters the caller actually supplied.
    # Note every VALUE is a bind parameter; only names WE wrote are interpolated.
    clauses: list[str] = []
    params: dict = {"limit": page.limit, "offset": page.offset}
    if city is not None:
        clauses.append("city = :city")
        params["city"] = city
    if from_date is not None:
        clauses.append("obs_date >= :from_date")
        params["from_date"] = from_date
    if to_date is not None:
        clauses.append("obs_date <= :to_date")
        params["to_date"] = to_date
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    sql = text(f"""
        SELECT city, obs_date, temp_max_c, temp_min_c, precip_mm
        FROM staging.weather_clean
        {where_sql}
        ORDER BY {column} {direction_sql}, city ASC
        LIMIT :limit OFFSET :offset
    """)
    return conn.execute(sql, params).mappings().all()


@router.get("/weekly", response_model=list[WeeklySummaryOut], summary="Weekly aggregates")
def read_weekly(
    city: str | None = Query(default=None, description="Filter to one city"),
    page: Pagination = Depends(pagination),
    conn: Connection = Depends(get_conn),
) -> list:
    """Pre-aggregated weekly rows straight from the marts layer.

    The aggregation already happened in SQL during the pipeline run, so this
    endpoint is a cheap read no matter how much raw data sits behind it.
    """
    clauses = "WHERE city = :city" if city is not None else ""
    params: dict = {"limit": page.limit, "offset": page.offset}
    if city is not None:
        params["city"] = city

    sql = text(f"""
        SELECT city, week_start, avg_temp_max_c, avg_temp_min_c,
               total_precip_mm, days_observed, temp_change_vs_prev_week_c
        FROM marts.weather_weekly
        {clauses}
        ORDER BY week_start DESC, city ASC
        LIMIT :limit OFFSET :offset
    """)
    return conn.execute(sql, params).mappings().all()


@router.get("/cities/{city}/stats", response_model=CityStatsOut, summary="One city's summary")
def read_city_stats(city: str, conn: Connection = Depends(get_conn)) -> dict:
    """Answer-shaped summary for a single city.

    Returns 404 when the city has no observations - a missing city is the
    caller's mistake, not a server error.
    """
    row = conn.execute(
        text("""
            WITH base AS (
                SELECT * FROM staging.weather_clean WHERE city = :city
            )
            SELECT
                :city                                  AS city,
                count(*)                               AS days_observed,
                min(obs_date)                          AS first_observation,
                max(obs_date)                          AS last_observation,
                (SELECT obs_date FROM base
                  WHERE temp_max_c IS NOT NULL
                  ORDER BY temp_max_c DESC, obs_date ASC LIMIT 1)   AS warmest_day,
                max(temp_max_c)                        AS warmest_temp_c,
                (SELECT obs_date FROM base
                  WHERE temp_min_c IS NOT NULL
                  ORDER BY temp_min_c ASC, obs_date ASC LIMIT 1)    AS coldest_day,
                min(temp_min_c)                        AS coldest_temp_c,
                round(sum(precip_mm), 1)               AS total_precip_mm
            FROM base
        """),
        {"city": city},
    ).mappings().first()

    if row is None or row["days_observed"] == 0:
        raise HTTPException(status_code=404, detail=f"No observations for city {city!r}")
    return dict(row)
