# nl-open-data-pipeline

A scheduled **ELT pipeline**: Dutch open weather data (Open-Meteo, incl. the KNMI reference
station De Bilt) → PostgreSQL → layered SQL transformations (**raw → staging → marts**) →
analytics. Runs nightly via GitHub Actions cron. Tested with pytest, linted with ruff.

```
Open-Meteo API ──► fetch.py ──► raw.weather_daily (JSONB, upsert)      Python (E + L)
                                       │
                                       ▼  sql/10_staging_weather.sql
                               staging.weather_clean (typed, filtered)  SQL (T)
                                       │
                                       ▼  sql/20_marts_weather.sql
                               marts.weather_weekly (aggregates, LAG)   SQL (T)
```

Key engineering properties (see Module 2, Day 6 theory):
- **Idempotent**: raw layer upserts on `(city, obs_date)`; derived layers rebuild from scratch —
  reruns can never duplicate data
- **Self-healing**: every run fetches an overlapping 7-day window, so missed runs and late
  corrections in the source fix themselves
- **Observable**: structured logs per step; scheduled runs visible in the Actions tab

## Quickstart

```bash
# 1. Database up (Docker Desktop running)
docker compose -f docker/docker-compose.yml up -d

# 2. Install (from this folder, with your module .venv active)
pip install -e ".[dev]"

# 3. Run the pipeline
python -m pipeline.run

# 4. Run the tests
pytest -v
```

Configuration via `.env` / environment: copy `.env.example` to `.env` (defaults match the Docker
setup, so locally you can skip this).

## Repository layout

```
src/pipeline/     config.py · fetch.py (E) · load.py (L) · transform.py (T) · run.py (entrypoint)
sql/              numbered transformation layers, run in order
tests/            unit tests (no network/DB) + integration tests (skip without DB)
.github/workflows ci.yml (lint+test on push) · pipeline.yml (daily cron, end-to-end run)
docker/           local PostgreSQL 16 + pgAdmin
```

---

> **📚 Learning this project as part of the course?** Open
> **[PROJECT_GUIDE.md](PROJECT_GUIDE.md)** — the full walkthrough: what every file does, why
> it's designed this way, your milestones, and a recipe for building similar pipelines yourself.

*Part of the [AI Engineer Path](../../README.md) — Module 2 portfolio project.*
