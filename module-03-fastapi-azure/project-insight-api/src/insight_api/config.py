"""Application settings.

Everything configurable lives here, so the rest of the code never reaches into
os.environ directly (same principle as Module 2's pipeline/config.py - but now
the values are validated, because Settings is a Pydantic model).

Precedence, highest first:
    1. a real environment variable   (how Azure and CI configure us)
    2. the .env file                 (how you configure your laptop)
    3. the default below             (so a fresh clone runs with zero setup)
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Points at the Module 2 stack by default.
    database_url: str = "postgresql+psycopg2://student:student123@localhost:5432/week2_db"

    app_name: str = "insight-api"
    app_version: str = "0.1.0"

    # Paging guardrails. A caller can never ask for more than max_page_size rows,
    # so one request can't drag the whole table across the network.
    default_page_size: int = 50
    max_page_size: int = 500

    # SQLAlchemy pool sizing. Keep this small: every replica gets its own pool,
    # and Postgres has a hard ceiling of ~100 connections in total. (Day 6)
    pool_size: int = 5
    max_overflow: int = 5


@lru_cache
def get_settings() -> Settings:
    """Build Settings once and reuse it.

    Without @lru_cache this would re-read .env from disk on every request.
    """
    return Settings()
