"""Central configuration for the pipeline.

Everything configurable lives here, so the rest of the code never reaches
into os.environ directly.
"""

import os

# Connection string; overridable via environment (used by CI and, later, Azure).
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://student:student123@localhost:5432/week2_db",
)

# Dutch cities we track: name -> (latitude, longitude).
# De Bilt is the KNMI reference station.
CITIES: dict[str, tuple[float, float]] = {
    "De Bilt": (52.10, 5.18),
    "Amsterdam": (52.37, 4.90),
    "Rotterdam": (51.92, 4.48),
    "Eindhoven": (51.44, 5.48),
    "Groningen": (53.22, 6.57),
    "Maastricht": (50.85, 5.69),
}

# Overlapping fetch window (days). Reruns + upserts make the overlap harmless
# and let the pipeline self-heal after missed runs.
WINDOW_DAYS = 7

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARIABLES = "temperature_2m_max,temperature_2m_min,precipitation_sum"
