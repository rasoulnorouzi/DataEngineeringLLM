"""Application entrypoint.

Run locally with:
    uvicorn insight_api.main:app --reload

In the container (see Dockerfile) uvicorn binds 0.0.0.0 so traffic from outside
the container can actually reach it.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine

from insight_api.config import get_settings
from insight_api.routers import health, weather

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("insight_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the engine once at startup, dispose of it once at shutdown.

    The engine holds a POOL of connections. Building it is expensive (DNS, TCP,
    auth), so it must not happen per request - but it also must not happen at
    import time, or merely importing this module would require a database and
    the unit tests could not run.
    """
    settings = get_settings()
    app.state.engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,       # cheap liveness check before handing out a pooled conn
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
    )
    logger.info("Engine created for %s", settings.app_name)
    yield
    app.state.engine.dispose()
    logger.info("Engine disposed")


settings = get_settings()

app = FastAPI(
    title="insight-api",
    version=settings.app_version,
    lifespan=lifespan,
    summary="Read-only HTTP access to Dutch open weather data.",
    description=(
        "Serves the layered Postgres warehouse built in Module 2 "
        "(`staging.weather_clean` and `marts.weather_weekly`). "
        "Callers never touch the database directly."
    ),
)

app.include_router(health.router)
app.include_router(weather.router)


@app.get("/", tags=["meta"], summary="Where to start")
def root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
