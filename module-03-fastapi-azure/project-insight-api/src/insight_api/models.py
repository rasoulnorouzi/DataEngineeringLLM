"""Response models - the plating standard.

Every field a caller receives is declared here. Anything the database returns
that is NOT declared here is dropped on the way out, which is why adding a
column to a table can never accidentally publish it.

model_config from_attributes=True lets these read SQLAlchemy rows directly
(row.city) instead of requiring dicts (row["city"]).

Declaring floats also does the Decimal conversion for us: Postgres NUMERIC
arrives in Python as Decimal, which json cannot serialise. Pydantic converts it
at the boundary so no handler has to think about it.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class HealthOut(BaseModel):
    status: str = Field(examples=["ok"])
    app: str
    version: str


class ReadinessOut(BaseModel):
    status: str = Field(examples=["ready"])
    database: str = Field(examples=["ok"])


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city: str
    first_observation: date
    last_observation: date
    days_observed: int


class DailyObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city: str
    obs_date: date
    temp_max_c: float | None
    temp_min_c: float | None
    precip_mm: float | None


class WeeklySummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city: str
    week_start: date
    avg_temp_max_c: float | None
    avg_temp_min_c: float | None
    total_precip_mm: float | None
    days_observed: int
    temp_change_vs_prev_week_c: float | None


class CityStatsOut(BaseModel):
    """A single answer-shaped summary for one city."""

    model_config = ConfigDict(from_attributes=True)

    city: str
    days_observed: int
    first_observation: date
    last_observation: date
    warmest_day: date | None
    warmest_temp_c: float | None
    coldest_day: date | None
    coldest_temp_c: float | None
    total_precip_mm: float | None
