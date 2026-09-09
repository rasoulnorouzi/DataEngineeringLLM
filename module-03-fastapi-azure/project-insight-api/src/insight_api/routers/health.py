"""Health endpoints.

Two endpoints, two different questions - see Day 4:

    /health        LIVENESS   "is the process alive?"      -> failure means RESTART me
    /health/ready  READINESS  "can I actually serve?"      -> failure means STOP ROUTING to me

Liveness deliberately touches nothing. If it checked the database, a brief
database blip would make the orchestrator restart every container at exactly
the moment the database is least able to cope with a reconnect storm.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Connection, text

from insight_api.config import Settings, get_settings
from insight_api.deps import get_conn
from insight_api.models import HealthOut, ReadinessOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut, summary="Liveness probe")
def health(settings: Settings = Depends(get_settings)) -> dict:
    """Am I alive? No dependencies are checked on purpose."""
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@router.get("/health/ready", response_model=ReadinessOut, summary="Readiness probe")
def readiness(conn: Connection = Depends(get_conn)) -> dict:
    """Can I serve? Fails with 503 when the database is unreachable.

    503, not 500: the service itself is fine, a dependency is not. (Day 1)
    """
    try:
        conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any failure here means "not ready"
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready", "database": "ok"}
