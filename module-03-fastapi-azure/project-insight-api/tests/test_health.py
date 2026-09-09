"""Health endpoints: the liveness/readiness split from Day 4."""


def test_liveness_is_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_liveness_needs_no_database(broken_db_client):
    """Liveness must stay green when the database is down.

    If it didn't, a brief database blip would restart every container at the
    worst possible moment.
    """
    assert broken_db_client.get("/health").status_code == 200


def test_readiness_is_ready(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "database": "ok"}


def test_readiness_reports_503_when_database_is_down(broken_db_client):
    """503, not 500: we are fine, our dependency is not. (Day 1)"""
    r = broken_db_client.get("/health/ready")
    assert r.status_code == 503
    assert "database" in r.json()["detail"]


def test_root_points_at_the_docs(client):
    body = client.get("/").json()
    assert body["docs"] == "/docs"


def test_openapi_schema_is_generated(client):
    """The docs are derived from the code, so they cannot drift. Prove it."""
    schema = client.get("/openapi.json").json()
    assert "/weather/daily" in schema["paths"]
    assert "/health" in schema["paths"]
