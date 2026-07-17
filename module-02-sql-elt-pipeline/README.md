# Module 2 — SQL, Docker & a Scheduled ELT Pipeline

**Duration:** 2 weeks (~10 hrs/week) · **Status:** 📗 fully authored

By the end of this module you can: query and design relational data in PostgreSQL, run
infrastructure with Docker, and build a **real, scheduled ELT pipeline** that ingests Dutch
open data every day — your first deployable portfolio project.

> **Lost? Follow the route below top-to-bottom. Every step names the exact file to open.
> Never skip a ☑ box.**

---

## 🧭 Your Route Through This Module

### Step 0 — Setup (~30 min, do once)

- [ ] Install Docker Desktop and start it. Never used Docker? Read
      [docs/DOCKER_GUIDE.md](../docs/DOCKER_GUIDE.md) first (~45 min extra, worth it).
- [ ] Create the module environment:

```bash
cd module-02-sql-elt-pipeline
python -m venv .venv
.venv\Scripts\activate              # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

- [ ] Start the database:

```bash
cd project-nl-open-data-pipeline
docker compose -f docker/docker-compose.yml up -d
docker ps        # expect: week2_postgres (healthy) + week2_pgadmin
```

- [ ] Open pgAdmin at http://localhost:8080 (`student@example.com` / `admin`) and confirm you
      can see the `week2_db` database. Connection details you'll reuse everywhere:
      host `localhost`, port `5432`, db `week2_db`, user `student`, password `student123`.

**Checkpoint:** `docker ps` shows both containers → you're ready for Day 1.

### Week A — SQL Foundations (Days 1–5, ~2h each)

Same rhythm every day: **read theory → run notebook → do exercise**. Open files in this exact order:

- [ ] **Day 1** — what a database is + first queries
      1. Read [lessons/day1-setup-and-basics/01_theory_what_is_a_database.md](lessons/day1-setup-and-basics/01_theory_what_is_a_database.md)
      2. Notebook [lessons/day1-setup-and-basics/02_first_queries.ipynb](lessons/day1-setup-and-basics/02_first_queries.ipynb)
      3. Exercise [exercises/exercise_1_basic_queries.ipynb](exercises/exercise_1_basic_queries.ipynb)
- [ ] **Day 2** — JOINs
      1. Read [lessons/day2-joins/03_theory_joins_explained.md](lessons/day2-joins/03_theory_joins_explained.md)
      2. Notebook [lessons/day2-joins/04_joins_practice.ipynb](lessons/day2-joins/04_joins_practice.ipynb)
      3. Exercise [exercises/exercise_2_joins_challenge.ipynb](exercises/exercise_2_joins_challenge.ipynb)
- [ ] **Day 3** — GROUP BY, CTEs, subqueries
      1. Read [lessons/day3-grouping-and-subqueries/05_theory_aggregation.md](lessons/day3-grouping-and-subqueries/05_theory_aggregation.md)
      2. Notebook [lessons/day3-grouping-and-subqueries/06_groupby_ctes_subqueries.ipynb](lessons/day3-grouping-and-subqueries/06_groupby_ctes_subqueries.ipynb)
- [ ] **Day 4** — window functions
      1. Read [lessons/day4-window-functions/07_theory_window_functions.md](lessons/day4-window-functions/07_theory_window_functions.md)
      2. Notebook [lessons/day4-window-functions/08_window_functions_practice.ipynb](lessons/day4-window-functions/08_window_functions_practice.ipynb)
      3. Exercise [exercises/exercise_3_window_functions.ipynb](exercises/exercise_3_window_functions.ipynb)
- [ ] **Day 5** — indexing + DuckDB
      1. Read [lessons/day5-indexing-and-duckdb/09_theory_indexing.md](lessons/day5-indexing-and-duckdb/09_theory_indexing.md)
      2. Notebook [lessons/day5-indexing-and-duckdb/10_indexing_practice.ipynb](lessons/day5-indexing-and-duckdb/10_indexing_practice.ipynb)
      3. Read [lessons/day5-indexing-and-duckdb/11_theory_duckdb_intro.md](lessons/day5-indexing-and-duckdb/11_theory_duckdb_intro.md)
      4. Notebook [lessons/day5-indexing-and-duckdb/12_duckdb_practice.ipynb](lessons/day5-indexing-and-duckdb/12_duckdb_practice.ipynb)
      5. Exercise [exercises/exercise_4_duckdb_analytics.ipynb](exercises/exercise_4_duckdb_analytics.ipynb)

**Checkpoint:** you can explain JOIN vs GROUP BY vs window function in one sentence each.

### Week B — From Queries to a Pipeline (Days 6–10)

- [ ] **Day 6 (~2h)** — how real pipelines are organized
      1. Read [lessons/day6-elt-and-layered-sql/13_theory_elt_and_layered_sql.md](lessons/day6-elt-and-layered-sql/13_theory_elt_and_layered_sql.md)
         (ETL vs ELT, idempotency, raw/staging/marts, dbt-in-concept)
- [ ] **Day 7 (~2.5h)** — get data from APIs
      1. Read [lessons/day7-ingestion-from-apis/14_theory_apis_and_ingestion.md](lessons/day7-ingestion-from-apis/14_theory_apis_and_ingestion.md)
      2. Notebook [lessons/day7-ingestion-from-apis/15_ingestion_practice.ipynb](lessons/day7-ingestion-from-apis/15_ingestion_practice.ipynb)
         — ingest live Dutch weather into YOUR database
- [ ] **Day 8 (~2.5h)** — testing + CI (bridge lesson)
      1. Skim [docs/GIT_GITHUB_GUIDE.md](../docs/GIT_GITHUB_GUIDE.md) if Git feels shaky
      2. Read [lessons/day8-testing-and-ci/16_theory_pytest_and_github_actions.md](lessons/day8-testing-and-ci/16_theory_pytest_and_github_actions.md)
- [ ] **Days 9–10 (~3h)** — THE PROJECT
      1. Open [project-nl-open-data-pipeline/PROJECT_GUIDE.md](project-nl-open-data-pipeline/PROJECT_GUIDE.md)
         — the full learner guide: what it is, how to run it, every file explained, and how to
         build one yourself. Work through its Parts 1→5.
      2. Finish with its milestones (extend the pipeline, publish to GitHub, green CI badge).

---

## 🏆 Portfolio Project: `nl-open-data-pipeline`

Scheduled ingest of Dutch weather data (Open-Meteo API, incl. KNMI reference station De Bilt) →
Dockerized PostgreSQL → layered SQL (**raw → staging → marts**) → weekly analytics. Tested with
pytest, CI + nightly cron via GitHub Actions.

Two documents, two purposes:
- [PROJECT_GUIDE.md](project-nl-open-data-pipeline/PROJECT_GUIDE.md) — **for you, the learner**: full walkthrough & explanations
- [README.md](project-nl-open-data-pipeline/README.md) — **for recruiters/visitors**: what ships with the repo when you publish it

> *CV bullet:* "Designed a scheduled ELT pipeline ingesting Dutch open data into Dockerized
> PostgreSQL with layered SQL transformations and automated nightly runs."

---

## ✅ Definition of Done

- [ ] Every checkbox above ticked
- [ ] `python -m pipeline.run` succeeds locally; running it twice does NOT duplicate rows
- [ ] `pytest -v` green in the project folder (6 tests, 0 skipped while Docker runs)
- [ ] Project published as your own public GitHub repo, CI badge green, scheduled workflow enabled

Then report "Module 2 done" so [PLAN.md](../PLAN.md) gets updated — and ask for **Module 3**.
