"""Pipeline entrypoint: fetch -> load -> transform.

Run with:  python -m pipeline.run
"""

import logging
import sys

from sqlalchemy import create_engine, text

from pipeline import config, fetch, load, transform

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")


def main() -> int:
    engine = create_engine(config.DATABASE_URL)

    logger.info("Step 1/3: extract - fetching %d cities", len(config.CITIES))
    records = fetch.fetch_all()

    logger.info("Step 2/3: load - upserting into raw layer")
    load.ensure_raw_schema(engine)
    load.upsert_raw(engine, records)

    logger.info("Step 3/3: transform - rebuilding staging and marts")
    executed = transform.run_sql_files(engine)
    logger.info("Transformations run: %s", ", ".join(executed))

    # Small final report so the run log (and the GitHub Actions log) shows proof of life.
    with engine.connect() as conn:
        raw_n = conn.execute(text("SELECT count(*) FROM raw.weather_daily")).scalar()
        mart_n = conn.execute(text("SELECT count(*) FROM marts.weather_weekly")).scalar()
    logger.info("Done. raw.weather_daily=%s rows, marts.weather_weekly=%s rows", raw_n, mart_n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
