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

## 🎓 Your Milestones (Days 9–10 of Module 2)

Work through these in order. Don't skip Milestone 1 — reading code you didn't write is half of
every engineering job.

### Milestone 1 — Run it and trace it (~45 min)
Run the quickstart. Then read the code in this order: `run.py` → `config.py` → `fetch.py` →
`load.py` → `transform.py` → both `sql/` files. For each file, say out loud (really) which
Day 6–8 concept it implements. Verify in pgAdmin that `raw`, `staging`, and `marts` schemas exist
and `marts.weather_weekly` has data.

### Milestone 2 — Prove idempotency (~15 min)
Run `python -m pipeline.run` twice in a row. Check row counts don't change. Then run `pytest -v`
and find the test that proves the same thing.

### Milestone 3 — Extend it (~1.5 h)
Add a new mart: `marts.city_rankings` — for each week, rank cities by `total_precip_mm`
(wettest first) using a window function. Add it as `sql/30_marts_rankings.sql` and rerun.

<details>
<summary>💡 Hint</summary>

`RANK() OVER (PARTITION BY week_start ORDER BY total_precip_mm DESC)` over
`marts.weather_weekly`. Remember: new derived table = DROP + CREATE AS SELECT, and the filename
number controls execution order.
</details>

<details>
<summary>✅ Solution</summary>

```sql
CREATE SCHEMA IF NOT EXISTS marts;

DROP TABLE IF EXISTS marts.city_rankings;

CREATE TABLE marts.city_rankings AS
SELECT
    week_start,
    city,
    total_precip_mm,
    RANK() OVER (PARTITION BY week_start ORDER BY total_precip_mm DESC) AS precip_rank
FROM marts.weather_weekly
ORDER BY week_start, precip_rank;
```
</details>

### Milestone 4 — Test your extension (~45 min)
Add a test to `tests/test_db_integration.py` asserting that after `run_sql_files`, the new
`marts.city_rankings` table exists and Testville has rank 1 (it's the only city in test data).
Update the `executed == [...]` assertion too.

### Milestone 5 — Publish it (~1 h)
Follow [docs/GIT_GITHUB_GUIDE.md](../../docs/GIT_GITHUB_GUIDE.md) → "Publishing a course project":
copy this folder to its own public repo, push, watch `ci.yml` go green, add the badge to the
README, then trigger `pipeline.yml` manually (Actions tab → Run workflow) and enjoy your first
scheduled production-style pipeline run.

### Stretch goals (optional)
- Swap Open-Meteo for the official **KNMI Data Platform API** (free key required — real-world auth)
- Add a DuckDB notebook reading `marts.*` for charts (Day 5 skills)
- Add `ruff format` as a CI step

---

*Part of the [AI Engineer Path](../../README.md) — Module 2 portfolio project.*
