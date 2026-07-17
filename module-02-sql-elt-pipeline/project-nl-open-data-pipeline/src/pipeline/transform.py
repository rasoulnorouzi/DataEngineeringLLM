"""Transform step: run the layered SQL files (staging, then marts) in order.

Each .sql file rebuilds its layer from the layer below (Day 6: derived tables
get rebuilt, raw gets upserts). Files run in filename order - that's why they
are numbered 10_, 20_, ...
"""

import logging
from pathlib import Path

from sqlalchemy import Engine

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"


def run_sql_files(engine: Engine, sql_dir: Path = SQL_DIR) -> list[str]:
    """Execute every *.sql file in sql_dir in sorted (numbered) order."""
    executed = []
    for sql_file in sorted(sql_dir.glob("*.sql")):
        logger.info("Running %s", sql_file.name)
        with engine.begin() as conn:
            conn.exec_driver_sql(sql_file.read_text(encoding="utf-8"))
        executed.append(sql_file.name)
    return executed
