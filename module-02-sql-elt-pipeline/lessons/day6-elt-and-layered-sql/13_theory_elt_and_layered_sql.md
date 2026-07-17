# Day 6 Theory: ELT & Layered SQL — How Real Data Pipelines Are Organized

**Time:** ~1.5 hours reading + thinking
**Prerequisites:** Week A (especially CTEs from Day 3 and window functions from Day 4)

---

## 1. Why This Lesson Exists

So far you've written *queries*: you ask the database a question, it answers, done.
Real data engineering is different: data **keeps arriving** — every hour, every night — and it
arrives **messy**. Your job becomes building a *machine* that repeatedly:

1. Fetches new data from somewhere (an API, files, another database)
2. Stores it safely
3. Cleans and reshapes it
4. Produces tables that analysts, dashboards — and later in this course, **AI agents** — can trust

That machine is a **pipeline**. This lesson gives you the three ideas every professional pipeline
is built on: **ELT**, **idempotency**, and **layers**.

---

## 2. ETL vs ELT: Where Does the "T" Happen?

Both acronyms contain the same three steps:

- **E**xtract — get data out of the source (call the API, read the file)
- **T**ransform — clean, reshape, join, aggregate
- **L**oad — write into your database/warehouse

The only difference is the **order** — and it changes everything.

### ETL (the old way)

```
API ──► [Python script transforms everything in memory] ──► clean tables in DB
```

Transform *before* loading. Your Python script fetches data, cleans it, fixes types, joins,
aggregates — and only the polished result ever touches the database.

**The problem — an analogy:** imagine a crime lab that throws away the original evidence and only
keeps the typed summary report. If the report has a mistake, or next month someone asks a new
question ("was there mud on the shoes?"), the evidence is *gone*. You'd have to hope the crime
happens again.

In ETL, if your transformation has a bug (they always do), or requirements change ("actually we
also need the wind speed"), you must re-fetch everything from the source. Sources disappear, APIs
have rate limits, history gets deleted. Data you didn't save is data you lost.

### ELT (the modern way — what we build)

```
API ──► load RAW data into DB, untouched ──► transform INSIDE the DB with SQL
```

Load *first*, exactly as received. Transform afterwards, in SQL, inside the database.

**Why this wins:**

| | ETL | ELT |
|---|---|---|
| Original data | discarded after transform | kept forever in raw tables |
| Transform has a bug? | re-fetch everything (maybe impossible) | re-run SQL over raw data — seconds |
| New requirement? | change code, re-fetch | write new SQL over data you already have |
| Transform language | Python in a script somewhere | SQL, versioned, reviewable, testable |

Storage became cheap; source data stayed precious. So we hoard the raw data and treat
transformations as *disposable and re-runnable*. That's ELT.

> **You already know the "T" language.** Everything from Week A — JOINs, GROUP BY, CTEs, window
> functions — *is* the transform step. ELT is where those skills become production skills.

---

## 3. Idempotency: The Most Important Word in This Module

A pipeline step is **idempotent** if running it *twice* produces the same result as running it
*once*.

**Analogy — the light switch vs the staircase.** Pressing a light switch's "ON" position ten times
leaves the light simply ON — idempotent. Climbing "one step up" ten times leaves you ten steps
higher — NOT idempotent. Pipelines must be light switches, never staircases.

Why? Because pipelines **fail and get retried**. The network drops mid-run. The scheduler fires
twice. A colleague reruns yesterday's job "just to be safe." If your load step is a staircase,
every retry *duplicates data*:

```sql
-- ❌ BAD: the staircase. Run it twice → every row exists twice → all your
-- averages, counts and dashboards are silently wrong.
INSERT INTO raw.weather (city, date, temp_max)
VALUES ('De Bilt', '2026-07-16', 24.1);
```

```sql
-- ✅ GOOD: the light switch (an "UPSERT").
-- A unique constraint on (city, date) + ON CONFLICT:
-- first run inserts; any rerun just overwrites with the same values.
INSERT INTO raw.weather (city, date, temp_max)
VALUES ('De Bilt', '2026-07-16', 24.1)
ON CONFLICT (city, date)
DO UPDATE SET temp_max = EXCLUDED.temp_max;
```

`EXCLUDED` is Postgres-speak for "the row I just tried to insert."

The second idempotency pattern you'll use is for *derived* tables:

```sql
-- ✅ GOOD: rebuild-from-scratch. Deleting + recreating from raw data
-- always gives the same result, no matter how often you run it.
DROP TABLE IF EXISTS staging.weather_clean;
CREATE TABLE staging.weather_clean AS
SELECT ... FROM raw.weather ...;
```

Rule of thumb: **raw tables get UPSERTs, derived tables get rebuilt.**
(At big-data scale you'd rebuild *incrementally* — only recent partitions — but the principle is
identical, and our data is small enough to rebuild fully.)

### Incremental loads

Related idea: don't re-fetch *everything* from the source every night — fetch only what's new
(e.g., "give me the last 7 days"). Combined with UPSERT, a 7-day overlapping window is a classic,
robust pattern: recent corrections in the source get picked up, duplicates are impossible, and a
few days of missed runs heal themselves. Your project uses exactly this.

---

## 4. The Three Layers: raw → staging → marts

Professional warehouses organize tables into layers. We use PostgreSQL **schemas** (namespaces you
met on Day 1) to keep them apart:

```
┌────────────────────────────────────────────────────────────────┐
│  raw.*        "the evidence locker"                            │
│               Data EXACTLY as received. JSON blobs, wrong      │
│               types, duplicates — all fine. Never edited,      │
│               only appended/upserted. Nobody queries this      │
│               except the staging layer.                        │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼  SQL (types, renames, dedup, filters)
┌────────────────────────────────────────────────────────────────┐
│  staging.*    "the cleaning station"                           │
│               One row = one real-world fact. Correct types,    │
│               clear column names, invalid rows filtered out.   │
│               Still detail-level, no business logic yet.       │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼  SQL (joins, aggregates, window functions)
┌────────────────────────────────────────────────────────────────┐
│  marts.*      "the shop window"                                │
│               Answer-shaped tables for consumers: weekly       │
│               summaries, rankings, trends. What dashboards,    │
│               notebooks and (later) AI agents actually query.  │
└────────────────────────────────────────────────────────────────┘
```

**Why not one big table?** Same reason kitchens separate the fridge, the cutting board, and the
serving plate. If a transformation is wrong, you fix one layer and rebuild downstream — the
evidence in `raw` is untouched. If a consumer's numbers look weird, you can trace them backwards
layer by layer. Debugging becomes *walking through rooms* instead of *archaeology*.

Each layer transition is just a `.sql` file full of the SQL you already know:

- `raw → staging`: casts (`::numeric`, `::date`), renames, `WHERE` filters, deduplication with
  `ROW_NUMBER()` (Day 4!)
- `staging → marts`: `GROUP BY` aggregates (Day 3), `JOIN`s (Day 2), `LAG()` for week-over-week
  change (Day 4)

---

## 5. dbt in Concept (so you can talk about it in interviews)

If you read Dutch data job postings you'll see **dbt** ("data build tool") everywhere in
analytics-engineer roles. Here's the honest summary:

**dbt is a framework for exactly what you're building by hand.** Each `SELECT` becomes a "model"
file; dbt figures out the dependency order (staging before marts), runs them, and adds:

- `ref()` — models reference each other by name instead of hardcoded schema names
- built-in tests (`not_null`, `unique`) declared in YAML
- auto-generated documentation and lineage graphs (which table feeds which)

That's genuinely useful at a company with 500 models and 10 people editing them. For one pipeline
with three SQL files, dbt is a forklift for a grocery bag. **This course teaches the concepts by
hand** — layers, idempotent rebuilds, dependency order, tested transformations — because the
concepts are what interviews probe. If a job needs dbt, you'll learn the tool in a day, since you
already *are* a dbt pipeline, manually.

Interview-ready sentence: *"I built layered ELT pipelines (raw/staging/marts) with idempotent
loads and tested SQL transformations — hand-rolled rather than dbt, so I understand exactly what
dbt automates."*

---

## 6. Orchestration: Who Presses "Run" Every Night?

A pipeline nobody runs is a script. Something must execute it on schedule — that's
**orchestration**. The industry-famous tool is **Apache Airflow**; for our scale it is (again) a
forklift for a grocery bag. We use two simpler, very employable tools:

1. **A plain Python entrypoint** (`python -m pipeline.run`) that calls fetch → load → transform in
   order and logs each step. Readable, debuggable, testable.
2. **GitHub Actions cron** — the same CI service you'll meet on Day 8 can also run a workflow on a
   schedule (e.g., daily at 06:00). Free, visible run history, email on failure.

Concepts that transfer straight to Airflow if a job ever needs it: steps in dependency order,
retries, idempotency (so retries are safe), logging, alerting on failure.

---

## 7. Summary — the vocabulary you now own

- **ELT**: load raw first, transform inside the database with SQL. Raw data is precious; keep it.
- **Idempotent**: running twice == running once. UPSERT for raw, rebuild for derived tables.
- **Incremental load**: fetch only a recent window, overlap it, upsert — self-healing.
- **raw / staging / marts**: evidence locker → cleaning station → shop window.
- **dbt**: industrializes this exact pattern; you're learning the concepts by hand.
- **Orchestration**: a scheduler pressing "run" — ours is GitHub Actions cron.

**Next (Day 7):** where the data actually comes from — HTTP APIs and JSON, and your first live
ingestion of Dutch weather data.
