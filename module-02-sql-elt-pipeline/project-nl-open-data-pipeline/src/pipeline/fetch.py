"""Extract step: fetch daily weather from the Open-Meteo archive API."""

import json
import logging
import time
from datetime import date, timedelta

import requests

from pipeline import config

logger = logging.getLogger(__name__)


def date_window(today: date, days: int = config.WINDOW_DAYS) -> tuple[date, date]:
    """Return the (start, end) fetch window: the `days` days ending yesterday.

    Yesterday, not today: today's data is still incomplete in the archive.
    """
    end = today - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start, end


def reshape_daily(daily: dict) -> list[dict]:
    """Turn Open-Meteo's parallel arrays into one dict per day.

    The API is column-oriented ({"time": [...], "temperature_2m_max": [...]});
    our raw table wants one row per day.
    """
    # strict=True: if the API ever returns arrays of different lengths, that is corrupt
    # source data - fail loudly rather than silently dropping the extra days.
    return [
        {"obs_date": d, "temp_max": tmax, "temp_min": tmin, "precip_mm": prec}
        for d, tmax, tmin, prec in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_sum"],
            strict=True,
        )
    ]


def fetch_city(city: str, lat: float, lon: float, start: date, end: date) -> list[dict]:
    """Fetch one city's daily weather and return upsert-ready records."""
    response = requests.get(
        config.OPEN_METEO_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": config.DAILY_VARIABLES,
            "timezone": "Europe/Amsterdam",
        },
        timeout=30,
    )
    response.raise_for_status()
    days = reshape_daily(response.json()["daily"])
    return [
        {
            "city": city,
            "obs_date": day["obs_date"],
            "payload": json.dumps(
                {
                    "temp_max": day["temp_max"],
                    "temp_min": day["temp_min"],
                    "precip_mm": day["precip_mm"],
                }
            ),
        }
        for day in days
    ]


def fetch_all(today: date | None = None) -> list[dict]:
    """Fetch the window for every configured city (politely: 0.5s between calls)."""
    start, end = date_window(today or date.today())
    records: list[dict] = []
    for city, (lat, lon) in config.CITIES.items():
        rows = fetch_city(city, lat, lon, start, end)
        logger.info("Fetched %s: %d days (%s..%s)", city, len(rows), start, end)
        records.extend(rows)
        time.sleep(0.5)
    return records
