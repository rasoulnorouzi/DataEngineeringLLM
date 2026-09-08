# insight-api

[![CI](https://github.com/your-username/insight-api/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/insight-api/actions/workflows/ci.yml)

A containerized **FastAPI** service that exposes a layered PostgreSQL warehouse of Dutch open weather
data over a typed, documented, read-only HTTP API — deployed to **Azure Container Apps** by a CI/CD
pipeline that runs on every merge.

> Replace `your-username` in the badge above, and add your live URL here once deployed.

---

## What it does

Dutch weather observations are ingested into PostgreSQL by a scheduled ELT pipeline and refined
through `raw → staging → marts`. This service puts a public counter in front of that warehouse:
callers get answer-shaped JSON, and nobody gets a database credential.

| Endpoint | Returns |
|---|---|
| `GET /health` | Liveness — no dependencies checked |
| `GET /health/ready` | Readiness — `503` when the database is unreachable |
| `GET /weather/cities` | Cities with data and the period they cover |
| `GET /weather/daily` | Daily observations; filter by city and date range, sort, page |
| `GET /weather/weekly` | Weekly aggregates, including week-over-week temperature change |
| `GET /weather/cities/{city}/stats` | One city's summary; `404` if unknown |

Interactive OpenAPI docs at `/docs`, generated from the code rather than maintained beside it.

## Architecture

```
Open-Meteo API ──▶ ELT pipeline ──▶ PostgreSQL ──▶ insight-api ──▶ clients
                    (scheduled)     raw            (FastAPI)       HTTPS
                                    staging  ◀── read-only
                                    marts
```

Deployed as a single container image to Azure Container Apps, scaling to zero when idle. Images are
built in Azure Container Registry and tagged with the commit SHA, so every running revision maps to
an exact diff and rollback is a one-command revision switch.

## Tech

**FastAPI** · **Pydantic v2** · **SQLAlchemy Core** · **PostgreSQL 16** · **Docker** (multi-stage,
non-root) · **pytest** · **ruff** · **GitHub Actions** · **Azure Container Apps** with OIDC
federated credentials (no stored secrets).

## Quickstart

The whole stack — API plus a seeded PostgreSQL — with one command:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Then open <http://localhost:8000/docs>.

Running it directly against an existing warehouse:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
export DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/db"
uvicorn insight_api.main:app --reload
```

## Tests

```bash
pytest -v          # unit tests need nothing; integration tests skip without a database
ruff check .
```

CI runs both as separate jobs — the integration job brings up a PostgreSQL service container, seeds
it from `sql/seed_test_data.sql`, and **fails the build if the integration tests skip**, so a green
badge always means the SQL actually ran.

## Layout

```
src/insight_api/
  config.py      typed settings (environment > .env > default)
  deps.py        injected dependencies: pooled connection, pagination
  models.py      response models — an allow-list for everything that leaves
  main.py        app assembly; engine created once via lifespan
  routers/       health.py, weather.py
tests/           unit (fake database) + integration (real SQL)
sql/             warehouse fixture for CI and local runs
docker/          compose stack
.github/workflows/  ci.yml (lint + test), cd.yml (build + deploy)
```

## Design notes

- **Handlers are `def`, not `async def`.** The PostgreSQL driver is blocking, so FastAPI runs them in
  a threadpool. Blocking code inside `async def` would stall the event loop for every request.
- **Every caller value is a bind parameter.** Identifiers can't be bound, so sortable columns come
  from a server-side allow-list — a caller supplies a key, never a column name.
- **Response models filter, convert, validate and document.** A column added to the database cannot
  leak into a response, and `NUMERIC` → `Decimal` is converted at the boundary.
- **Liveness and readiness are separate.** Liveness has no dependencies, so a database blip stops
  traffic being routed rather than triggering a restart storm.

---

Built as the Module 3 portfolio project of an AI-engineering curriculum. Course learners: see
[PROJECT_GUIDE.md](PROJECT_GUIDE.md) for the full walkthrough and milestones.
