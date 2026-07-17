# Module 2 — SQL, Docker & a Scheduled ELT Pipeline

**Duration:** 2 weeks (~10 hrs/week) · **Status:** 📗 fully authored

By the end of this module you can: query and design relational data in PostgreSQL, run
infrastructure with Docker, and build a **real, scheduled ELT pipeline** that ingests Dutch
open data every day — your first deployable portfolio project.

## Portfolio Project: [`nl-open-data-pipeline`](project-nl-open-data-pipeline/README.md)

Ingests Dutch weather data (Open-Meteo API, cities incl. De Bilt, Amsterdam, Rotterdam) into
Dockerized PostgreSQL on a schedule (GitHub Actions cron), transforms it through layered SQL
(**raw → staging → marts**), and serves analytics via DuckDB. Tested with pytest, linted and
CI-checked with GitHub Actions.

> *CV bullet:* "Designed a scheduled ELT pipeline ingesting Dutch open data into Dockerized
> PostgreSQL with layered SQL transformations and automated nightly runs."

---

## Setup (once)

```bash
cd module-02-sql-elt-pipeline
python -m venv .venv
.venv\Scripts\activate              # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt

# Start the database stack (Docker Desktop must be running)
cd project-nl-open-data-pipeline
docker compose -f docker/docker-compose.yml up -d
docker ps                            # expect week2_postgres + week2_pgadmin
```

Access: **pgAdmin** http://localhost:8080 (`student@example.com` / `admin`) ·
**PostgreSQL** localhost:5432, db `week2_db`, user `student`, pw `student123`.
Docker completely new to you? Read [docs/DOCKER_GUIDE.md](../docs/DOCKER_GUIDE.md) first.

---

## Week A — SQL Foundations (~10 hrs)

Daily pattern: 📖 theory → 💻 notebook → ✏️ exercise.

| Day | Folder | Topics | Time |
|-----|--------|--------|------|
| 1 | [lessons/day1-setup-and-basics](lessons/day1-setup-and-basics/) | What a database is, Docker setup, SELECT/WHERE/ORDER BY | ~2h |
| 2 | [lessons/day2-joins](lessons/day2-joins/) | INNER/LEFT/RIGHT/FULL JOINs | ~2h |
| 3 | [lessons/day3-grouping-and-subqueries](lessons/day3-grouping-and-subqueries/) | GROUP BY, HAVING, CTEs, subqueries | ~2h |
| 4 | [lessons/day4-window-functions](lessons/day4-window-functions/) | ROW_NUMBER, RANK, LAG/LEAD, frames | ~2h |
| 5 | [lessons/day5-indexing-and-duckdb](lessons/day5-indexing-and-duckdb/) | Indexes, EXPLAIN, DuckDB analytics | ~2h |

Extra practice: [exercises/](exercises/) (4 notebooks with collapsible solutions).

## Week B — From Queries to a Pipeline (~10 hrs)

| Day | Lesson | Topics | Time |
|-----|--------|--------|------|
| 6 | [lessons/day6-elt-and-layered-sql](lessons/day6-elt-and-layered-sql/) | ETL vs ELT, idempotency, incremental loads, raw/staging/marts, dbt-in-concept | ~2h |
| 7 | [lessons/day7-ingestion-from-apis](lessons/day7-ingestion-from-apis/) | HTTP APIs, JSON, requests, upserts — ingest live weather data | ~2.5h |
| 8 | [lessons/day8-testing-and-ci](lessons/day8-testing-and-ci/) | **Bridge lesson:** pytest from zero + your first GitHub Actions workflow (CI + cron) | ~2.5h |
| 9–10 | [project-nl-open-data-pipeline](project-nl-open-data-pipeline/README.md) | Build the project following its milestone guide; publish as your own repo | ~3h |

---

## Definition of Done

- [ ] All Week A notebooks run against your Docker Postgres; exercises attempted
- [ ] Week B lessons done: you can explain idempotency, raw/staging/marts, and what CI is
- [ ] `python -m pipeline.run` executes the full pipeline locally (fetch → load → transform)
- [ ] `pytest` green in the project folder
- [ ] Project published as your own public GitHub repo with a green CI badge and the scheduled
      workflow enabled

Then report back ("Module 2 done") so the tracker in [PLAN.md](../PLAN.md) gets updated, and ask
for **Module 3** to be authored.
