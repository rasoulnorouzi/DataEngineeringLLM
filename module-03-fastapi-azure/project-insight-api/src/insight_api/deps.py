"""Dependencies: the things handlers ask for instead of building.

Every function here exists so a handler can say `Depends(...)` - which is also
what lets the tests swap any of them for a fake without touching a handler.
"""

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy import Connection

from insight_api.config import Settings, get_settings


def get_conn(request: Request) -> Iterator[Connection]:
    """Borrow one pooled connection for the life of this request.

    The engine itself is created once, at startup, in main.lifespan - creating
    one per request would mean a new TCP connection and a new authentication
    handshake every time.

    `with` gives us the try/finally: the connection returns to the pool even if
    the handler raises.
    """
    engine = request.app.state.engine
    with engine.connect() as conn:
        yield conn


class Pagination:
    """limit/offset, validated once and reused by every list endpoint."""

    def __init__(self, limit: int, offset: int) -> None:
        self.limit = limit
        self.offset = offset


def pagination(
    limit: int | None = Query(default=None, ge=1, description="Rows to return"),
    offset: int = Query(default=0, ge=0, description="Rows to skip"),
    settings: Settings = Depends(get_settings),
) -> Pagination:
    """Turn ?limit=&offset= into a validated object.

    Defined once, used by every list endpoint - so the page-size policy lives in
    exactly one place and appears in /docs for all of them.
    """
    effective = settings.default_page_size if limit is None else limit
    if effective > settings.max_page_size:
        raise HTTPException(
            status_code=422,
            detail=f"limit must not exceed {settings.max_page_size}",
        )
    return Pagination(limit=effective, offset=offset)
