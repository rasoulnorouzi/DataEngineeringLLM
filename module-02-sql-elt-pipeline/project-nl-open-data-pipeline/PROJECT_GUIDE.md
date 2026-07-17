# 🎓 Project Guide — `nl-open-data-pipeline`

**This is your learner guide.** Read it top to bottom on Days 9–10 of Module 2. It explains what
this project is, how to run it, what every file does (with the code explained), why it's designed
this way, and — most importantly — **how you'd build a pipeline like this yourself** for any data
source.

*(The separate [README.md](README.md) is the "shop window" for recruiters when you publish this
as your own repo. This guide is the classroom.)*

**Route through this guide:**

| Part | What | Time |
|------|------|------|
| 1 | What is this project? | 10 min |
| 2 | Run it | 30 min |
| 3 | The big picture: architecture & one record's journey | 20 min |
| 4 | File-by-file code walkthrough | 60 min |
| 5 | Why it's designed this way | 20 min |
| 6 | Recipe: build your own pipeline for ANY source | 30 min |
| 7 | Milestones (your actual work) | ~3 h |
| 8 | Troubleshooting | as needed |

---

## Part 1 — What Is This Project?

In plain words: **a small program that, every day, automatically:**

1. **Fetches** yesterday's-and-the-last-week's weather for 6 Dutch cities from a free public API
2. **Loads** it into a PostgreSQL database, exactly as received, without ever creating duplicates
3. **Transforms** it with SQL into clean, analysis-ready tables (weekly averages, rainfall totals,
   week-over-week temperature change)

Plus the professional wrapper that makes it portfolio-worthy:

- **Tests** (pytest) that prove the logic works and STAYS working
- **CI** (GitHub Actions) that runs those tests on every push — the green badge
- **A schedule** (GitHub Actions cron) that runs the whole pipeline every morning without you

Everything you learned in Days 1–8 appears here: SQL (Days 1–5), ELT + idempotency + layers
(Day 6), API ingestion (Day 7), pytest + CI + cron (Day 8). The project is those lessons
**assembled into one machine.**

### Vocabulary check (from Day 6 — if any is fuzzy, re-read that lesson first)

- **ELT**: load raw data first, transform inside the database with SQL
- **Idempotent**: running twice gives the same result as running once
- **raw / staging / marts**: evidence locker → cleaning station → shop window

---

## Part 2 — Run It

Do this before reading any code. Seeing it work makes the code much easier to read.

### 2.1 Start the database

```bash
# From this folder (project-nl-open-data-pipeline), Docker Desktop running:
docker compose -f docker/docker-compose.yml up -d
docker ps
```

Expected: two containers, `week2_postgres` (status: healthy after ~15s) and `week2_pgadmin`.

### 2.2 Install the project

```bash
# With your module-02 .venv active:
pip install -e ".[dev]"
```

What this does: installs this folder as a Python package named `pipeline` (that's why
`python -m pipeline.run` works from anywhere), plus the dev tools (`pytest`, `ruff`).
The `-e` means "editable" — code changes take effect without reinstalling.

### 2.3 Run the pipeline

```bash
python -m pipeline.run
```

Expected output (times/numbers vary):

```
... INFO pipeline: Step 1/3: extract - fetching 6 cities
... INFO pipeline.fetch: Fetched De Bilt: 7 days (2026-07-10..2026-07-16)
... INFO pipeline.fetch: Fetched Amsterdam: 7 days (...)
    (4 more cities)
... INFO pipeline: Step 2/3: load - upserting into raw layer
... INFO pipeline.load: Upserted 42 records into raw.weather_daily
... INFO pipeline: Step 3/3: transform - rebuilding staging and marts
... INFO pipeline.transform: Running 10_staging_weather.sql
... INFO pipeline.transform: Running 20_marts_weather.sql
... INFO pipeline: Done. raw.weather_daily=42 rows, marts.weather_weekly=12 rows
```

### 2.4 Look at what it made

Open pgAdmin (http://localhost:8080) → Servers → week2_db → Schemas. You now have **three new
schemas**: `raw`, `staging`, `marts`. Run in the Query Tool:

```sql
SELECT * FROM marts.weather_weekly ORDER BY city, week_start;
```

That table — weekly temperatures per city with week-over-week change — is the pipeline's product.

### 2.5 The most important experiment: run it AGAIN

```bash
python -m pipeline.run
```

Check the final log line: **row counts unchanged.** That's idempotency (Day 6) — the property
that makes this pipeline safe to schedule, retry, and rerun. Remember this moment; Part 4 shows
the two lines of SQL that make it true.

### 2.6 Run the tests

```bash
pytest -v
```

Expected: **6 passed** (with Docker running). 4 are unit tests (pure logic, no network/DB),
2 are integration tests against your real Postgres.

---

## Part 3 — The Big Picture

### Architecture

```
           EXTRACT (Python)          LOAD (Python)              TRANSFORM (SQL)
┌──────────────┐   ┌────────────┐   ┌───────────────────┐   ┌──────────────────────┐
│  Open-Meteo  │──►│  fetch.py  │──►│ raw.weather_daily │──►│ staging.weather_clean │
│  archive API │   │            │   │  (JSONB, upsert)  │   │  (typed, filtered)    │
└──────────────┘   └────────────┘   └───────────────────┘   └──────────┬───────────┘
                                       load.py                          │ sql/10_...
                                                                        ▼
                                                            ┌──────────────────────┐
   WHO PRESSES RUN?                                         │ marts.weather_weekly │
   • you:              python -m pipeline.run               │ (aggregates, LAG)    │
   • GitHub Actions:   .github/workflows/pipeline.yml       └──────────────────────┘
     (cron, daily 05:00 UTC)                                   sql/20_...
```

### One record's journey (trace this — it's the whole project in miniature)

1. **06:00** — GitHub Actions cron fires `pipeline.yml` → runs `python -m pipeline.run`
2. `fetch.py` asks Open-Meteo: *"daily weather for De Bilt, last 7 days"* → gets JSON with
   parallel arrays → reshapes into records like
   `{"city": "De Bilt", "obs_date": "2026-07-16", "payload": '{"temp_max": 24.1, ...}'}`
3. `load.py` UPSERTs it into `raw.weather_daily`. If that (city, date) already exists from
   yesterday's run — and 6 of 7 days always do, that's the overlapping window — it's
   **overwritten, not duplicated**
4. `transform.py` runs `sql/10_staging_weather.sql`: rebuilds `staging.weather_clean` — the JSON
   payload becomes typed columns (`temp_max_c NUMERIC`), incomplete rows are filtered out
5. then `sql/20_marts_weather.sql`: rebuilds `marts.weather_weekly` — GROUP BY city+week,
   `LAG()` for week-over-week change
6. The Actions log shows `Done. raw.weather_daily=… rows` — green run in the Actions tab

Every arrow in the diagram is one file. That's the next part.

---

## Part 4 — File-by-File Walkthrough

Read the files in this order, guide alongside. Total: ~200 lines of Python — small on purpose.

```
project-nl-open-data-pipeline/
├── src/pipeline/
│   ├── config.py        ← 1. all settings in one place
│   ├── fetch.py         ← 2. Extract
│   ├── load.py          ← 3. Load
│   ├── transform.py     ← 4. Transform (runs the sql/ files)
│   └── run.py           ← 5. entrypoint gluing 2-3-4 together
├── sql/
│   ├── 10_staging_weather.sql   ← 6. raw → staging
│   └── 20_marts_weather.sql     ← 7. staging → marts
├── tests/               ← 8. unit + integration tests
├── .github/workflows/   ← 9. ci.yml (bouncer) + pipeline.yml (night shift)
├── docker/              ← local Postgres + pgAdmin (from Week A)
├── pyproject.toml       ← package definition: name, dependencies, dev tools
└── .env.example         ← template for configuration secrets
```

### 1. `src/pipeline/config.py` — settings in one place

```python
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://student:student123@localhost:5432/week2_db",
)
```

**The pattern:** read from the environment, fall back to a local-dev default. Locally you change
nothing; in GitHub Actions (and later Azure) the environment provides a different URL — **same
code, different config**. This is rule #3 of [the Twelve-Factor App](https://12factor.net/config),
the classic checklist for deployable software. Also here: the `CITIES` dict and `WINDOW_DAYS = 7`
(the overlap that makes the pipeline self-healing).

**Why a separate file?** So no other module ever touches `os.environ`. When config is scattered,
you can't tell what a program needs to run. When it's one file, that file IS the documentation.

### 2. `src/pipeline/fetch.py` — Extract

Three functions, each testable alone:

```python
def date_window(today, days=7) -> tuple[date, date]:
```
Pure date math: the 7 days ending **yesterday** (today's data is still incomplete in the
archive). Pure = no network, no database → trivially testable (`tests/test_fetch.py` proves it).

```python
def reshape_daily(daily: dict) -> list[dict]:
```
The API returns column-oriented parallel arrays (`"time": [...], "temperature_2m_max": [...]`);
we want one dict per day. `zip()` does the pivot — this is the exact code you wrote in the Day 7
notebook, promoted into a real module.

```python
def fetch_city(city, lat, lon, start, end) -> list[dict]:
```
The actual HTTP call, with the three Day-7 reflexes: `params=` dict, `timeout=30`,
`raise_for_status()`. Returns upsert-ready records where `payload` is the JSON string we'll store
raw. `fetch_all()` loops cities with `time.sleep(0.5)` between calls (polite API citizen).

### 3. `src/pipeline/load.py` — Load (where idempotency lives)

The two lines that make reruns safe:

```sql
ON CONFLICT (city, obs_date)
DO UPDATE SET payload = EXCLUDED.payload, loaded_at = now()
```

Because `raw.weather_daily` has `PRIMARY KEY (city, obs_date)`, inserting an existing (city, date)
doesn't error and doesn't duplicate — it **overwrites**. Run the pipeline 100 times: same rows.
(`EXCLUDED` = "the row I just tried to insert".) This + the 7-day overlapping window = missed
runs heal themselves and late corrections from the source get picked up. That's the light switch
from Day 6.

### 4. `src/pipeline/transform.py` — Transform

```python
for sql_file in sorted(sql_dir.glob("*.sql")):
    conn.exec_driver_sql(sql_file.read_text())
```

Deliberately tiny: find `sql/*.sql`, run them **in filename order** — which is why they're
numbered `10_`, `20_` (gaps left so `15_` can slot in later). The transformation *logic* lives in
SQL files, not Python, because SQL is reviewable, diffable, and it's what Day 6 taught: transform
inside the database. *(This numbered-SQL-files idea is exactly what dbt industrializes — you're
doing manually what dbt automates.)*

### 5. `src/pipeline/run.py` — the entrypoint

Reads top-to-bottom like the architecture diagram: fetch → load → transform, one log line per
step, and a final "proof of life" report (`Done. raw.weather_daily=42 rows...`). When the
scheduled run misbehaves at 6am, these logs in the Actions tab are how you'll know which step
died. `python -m pipeline.run` works because `pyproject.toml` installed `src/pipeline` as a
package.

### 6. `sql/10_staging_weather.sql` — raw → staging

```sql
DROP TABLE IF EXISTS staging.weather_clean;
CREATE TABLE staging.weather_clean AS
SELECT city, obs_date,
       (payload ->> 'temp_max')::numeric AS temp_max_c, ...
FROM raw.weather_daily
WHERE payload ->> 'temp_max' IS NOT NULL;
```

The second idempotency pattern (Day 6): **derived tables get rebuilt** — DROP + CREATE always
lands in the same state. `->>` reaches into the JSONB payload; `::numeric` casts text → number;
the `WHERE` is the data-quality gate dropping incomplete rows (the archive lags ~a day —
you saw the `null`s in the Day 7 notebook).

### 7. `sql/20_marts_weather.sql` — staging → marts

Week A on display: a CTE (Day 3) does `GROUP BY city, date_trunc('week', obs_date)` for weekly
averages; then `LAG(...) OVER (PARTITION BY city ORDER BY week_start)` (Day 4) computes
week-over-week temperature change. This is the "shop window" table consumers query — including
your Module 3 API and your Module 6 agent, later.

### 8. `tests/` — the smoke detectors

Two kinds, deliberately separated (Day 8):

- **`test_fetch.py` — unit tests.** Pure logic: date window math, reshaping. No network — the API
  response is a **saved fixture** (`tests/fixtures/open_meteo_sample.json`, loaded by
  `conftest.py` — `conftest.py` is pytest's "shared fixtures live here" file). Note the fixture
  has a `null` on purpose: tests pin down edge-case behavior.
- **`test_db_integration.py` — integration tests.** Need real Postgres. The key one runs the
  upsert **twice** and asserts the count didn't double — idempotency as an executable fact, not a
  promise. First lines ping the DB and `pytest.skip(...)` politely if Docker's down, so `pytest`
  never fails just because the database isn't running.

### 9. `.github/workflows/` — the robots

- **`ci.yml` (the bouncer):** on every push/PR → fresh Ubuntu machine → install → `ruff check`
  → `pytest`. This is the workflow from the Day 8 lesson, line for line.
- **`pipeline.yml` (the night shift):** `cron: "0 5 * * *"` + a manual Run-workflow button.
  Uses a GitHub Actions **service container** — a throwaway Postgres booted next to the job — and
  runs the REAL pipeline against the LIVE API end-to-end, then the integration tests. Green run
  every morning = "automated nightly runs" on your CV, with public run history as proof.
  *(Throwaway DB = data isn't kept between runs; in Module 3 this same workflow will point at a
  persistent Azure database.)*

---

## Part 5 — Why It's Designed This Way

Design decisions worth being able to defend in an interview:

| Decision | Why |
|---|---|
| `src/` layout with a package | `pip install -e .` + `python -m pipeline.run` work anywhere; imports (`from pipeline import config`) are clean; it's the modern Python standard recruiters' repos use |
| Fetch / load / transform as separate modules | Each testable alone; the run log tells you *which* step failed; swapping the data source touches only `fetch.py` |
| Transform in SQL files, not pandas | Day 6: the data is already in a database that's excellent at transformation; SQL files are diffable and reviewable; scales to dbt later |
| JSONB raw layer | Keep *everything* the API sent. New requirement next month? The data's already in the locker — no re-fetch |
| Upsert + overlapping window | Reruns safe, retries safe, missed weekend heals itself Monday, source corrections picked up |
| Unit vs integration tests split | Unit = fast, run anywhere (CI); integration = truth against real Postgres, skip gracefully without it |
| Config via environment | Same code runs on your laptop, in CI, and (Module 3) on Azure |

---

## Part 6 — The Recipe: Build a Pipeline Like This for ANY Source

This is the transferable skill. Next time you need "data from X into a database, on a schedule"
— at work, in an interview take-home, in your capstone — follow these steps:

1. **Find the natural key.** What uniquely identifies one record? (Here: city + date. For orders:
   order_id. For sensor data: sensor_id + timestamp.) This becomes your PRIMARY KEY and your
   `ON CONFLICT` target. *No natural key = no idempotency = start here, always.*
2. **Define the fetch window.** Full snapshot every run (small data)? Or incremental window
   (last N days/pages)? Overlap it a little — overlap + upsert = self-healing.
3. **Store raw first.** One table, natural key + `payload JSONB` + `loaded_at`. Resist the urge
   to "clean while loading" — that's ETL thinking (Day 6: the crime lab that shreds evidence).
4. **Write the upsert.** `INSERT ... ON CONFLICT (key) DO UPDATE`. Test the light switch: run
   twice, count once.
5. **Build staging.** One rebuilt table: types cast, names cleaned, junk filtered. One data-quality
   `WHERE` minimum.
6. **Build marts.** Ask: *what question should this data answer?* Write THAT table (GROUP BY,
   JOINs, window functions).
7. **Test the seams.** Unit-test your reshaping with a saved fixture; integration-test idempotency
   and that transforms produce the expected shape.
8. **Schedule it.** Cron workflow, logs per step, loud failure (GitHub emails you on red).

### Worked variation: CBS (Dutch statistics bureau) instead of weather

The Dutch open-data portal `opendata.cbs.nl` has an OData API (no key needed) — e.g., monthly
unemployment per province. The recipe maps 1:1:

| Recipe step | Weather pipeline | CBS variation |
|---|---|---|
| Natural key | (city, obs_date) | (province, period) |
| Window | last 7 days | last 3 periods (CBS revises recent months!) |
| Raw | payload JSONB | identical — CBS JSON rows into JSONB |
| Staging | cast temps to numeric | cast rates, map CBS codes → province names |
| Marts | weekly avg + LAG | month-over-month change + provincial ranking |

Only `fetch.py` and the two SQL files change. `load.py`, `transform.py`, `run.py`, both
workflows: **untouched**. That's what good structure buys you — and building this variation is
exactly the kind of "similar job" you can now do solo.

---

## Part 7 — Milestones (your actual Days 9–10 work)

### Milestone 1 — Run and trace (~45 min)
Do all of Part 2. Then re-read Part 3's "one record's journey" with pgAdmin open, and verify each
station: the record in `raw.weather_daily` (see the JSONB!), its typed twin in
`staging.weather_clean`, its week in `marts.weather_weekly`.

### Milestone 2 — Prove idempotency (~15 min)
Part 2.5 if you skipped it. Then find the test in `tests/test_db_integration.py` that proves the
same thing, and make it fail on purpose: comment out the `ON CONFLICT` clause in `load.py`, run
`pytest -v`, watch the detector scream, restore it. *(Breaking things on purpose is the fastest
way to understand what protects you.)*

### Milestone 3 — Extend with a new mart (~1.5 h)
Add `marts.city_rankings`: for each week, rank cities by `total_precip_mm` (wettest first) with a
window function. New file `sql/30_marts_rankings.sql`, rerun the pipeline.

<details>
<summary>💡 Hint</summary>

`RANK() OVER (PARTITION BY week_start ORDER BY total_precip_mm DESC)` over
`marts.weather_weekly`. New derived table = DROP + CREATE AS SELECT (Part 4.6 pattern), and the
filename number controls execution order.
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
In `tests/test_db_integration.py`: assert that after `run_sql_files`, `marts.city_rankings`
exists and Testville has `precip_rank = 1` (only city in test data). Update the
`executed == [...]` list assertion too.

<details>
<summary>✅ Solution</summary>

```python
def test_rankings_mart(engine):
    load.ensure_raw_schema(engine)
    load.upsert_raw(engine, SAMPLE_RECORDS)

    executed = transform.run_sql_files(engine)
    assert executed == [
        "10_staging_weather.sql",
        "20_marts_weather.sql",
        "30_marts_rankings.sql",
    ]

    with engine.connect() as conn:
        rank = conn.execute(
            text("SELECT precip_rank FROM marts.city_rankings WHERE city = 'Testville'")
        ).scalar()
    assert rank == 1
```

(And update the same `executed == [...]` assertion inside
`test_transform_builds_staging_and_marts`.)
</details>

### Milestone 5 — Publish (~1 h)
[docs/GIT_GITHUB_GUIDE.md](../../docs/GIT_GITHUB_GUIDE.md) → "Publishing a course project": copy
this folder out to its own public repo, push, watch `ci.yml` go green, add the badge to the
README, then Actions tab → "Scheduled pipeline run" → **Run workflow** and watch your pipeline
execute in the cloud, end-to-end. 🎉

### Stretch goals (optional)
- Swap in the official **KNMI Data Platform API** (free key — real-world auth experience)
- A DuckDB notebook charting `marts.*` (Day 5 skills)
- Apply the Part 6 recipe to CBS data — a second pipeline, fully yours

---

## Part 8 — Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `connection refused` on port 5432 | Postgres not up → `docker compose -f docker/docker-compose.yml up -d`; check `docker ps` |
| `docker: command not found` / pipe error | Docker Desktop not running → start it, wait for the whale |
| `No module named pipeline` | Project not installed in the ACTIVE venv → activate module venv, `pip install -e ".[dev]"` from this folder |
| Both integration tests SKIPPED | Same as row 1 — tests skip without a reachable DB by design |
| API returns nulls for newest day | Normal — archive lags ~a day; staging's `WHERE` filters them, next run's overlap fills them in |
| `429 Too Many Requests` | You looped without `sleep` → keep the 0.5s pause, wait a minute, rerun (idempotent = safe) |
| Scheduled workflow didn't run at 05:00 sharp | Normal — GitHub delays cron by minutes; also check the workflow is enabled in the Actions tab (forks/new repos need one manual enable) |
| `relation "marts.weather_weekly" does not exist` | Transform never ran → run `python -m pipeline.run` fully, check its log for the failing step |

Still stuck → ask Claude Code, pasting the exact error and the command you ran.
