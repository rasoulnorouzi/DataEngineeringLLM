# 🎓 Project Guide — `insight-api`

**For you, the learner.** This is the full walkthrough: what the project is, how to run it, how
every file works, why it's built this way, how to build one like it from scratch, and the milestones
that turn it into your portfolio piece.

> The other file, [README.md](README.md), is written for **recruiters and visitors** — the short
> pitch they see when you publish this folder as its own public repo.

**Time:** Days 9–10 of Module 3 (~3 h), plus the deploy.

---

## Part 1 — What is this project?

Module 2 built a warehouse: Dutch weather data landing in Postgres, cleaned into `staging`,
aggregated into `marts`. Useful — and reachable only by someone with the database password and
knowledge of your schema.

`insight-api` is the **counter** in front of it. An HTTP service that answers questions like
"what was the weather in Utrecht last week?" over the public internet, with:

- a documented, typed contract that browsers, phones, dashboards and LLM agents can all use
- **no** database credentials handed to anyone
- freedom to refactor the warehouse without breaking a single caller

```
Module 2                              Module 3 (this project)
┌──────────────┐                      ┌──────────────────┐
│ Open-Meteo   │                      │  Anyone, anywhere │
└──────┬───────┘                      └────────┬──────────┘
       │ pipeline                              │ HTTPS
       ▼                                       ▼
┌──────────────────────────┐            ┌─────────────┐
│ Postgres                 │◀───────────│ insight-api │
│  raw → staging → marts   │  read-only │  (FastAPI)  │
└──────────────────────────┘            └─────────────┘
```

### What you'll be able to say about it

> *"Developed and deployed a containerized FastAPI analytics service to Azure Container Apps with a
> full CI/CD pipeline — automated tests, lint, image build and deploy on merge — serving a layered
> PostgreSQL warehouse through a typed, documented, read-only API."*

### Vocabulary check (from Days 1–8)

If any of these are fuzzy, re-read that day before continuing.

| Term | One line | Day |
|---|---|---|
| Endpoint | One thing a caller can ask for | 1 |
| Idempotent | Doing it twice = doing it once | 1 |
| Path vs query parameter | *Which* thing vs *how* you want it | 2 |
| `response_model` | An allow-list for what leaves | 3 |
| Dependency injection | Ask, don't build | 4 |
| `dependency_overrides` | Swap a real dependency for a fake | 5 |
| Liveness vs readiness | *Restart me* vs *stop routing to me* | 4 |
| Blocking in `async def` | Freezes every request in the service | 6 |
| Layer caching | Least-changing lines first | 7 |
| Federated credential | A visitor badge instead of a copied key | 8 |

---

## Part 2 — Run it

### 2.1 Get a database

The API is read-only over the Module 2 warehouse. Two ways to have one:

**Option A — your real Module 2 pipeline** (best: real data, real volume)

```bash
cd module-02-sql-elt-pipeline/project-nl-open-data-pipeline
docker compose -f docker/docker-compose.yml up -d
python -m pipeline.run          # populates raw -> staging -> marts
```

**Option B — this project's own seeded stack** (fastest; a handful of rows)

```bash
cd module-03-fastapi-azure/project-insight-api
docker compose -f docker/docker-compose.yml up --build
```

Option B starts Postgres **and** the API together, seeds the warehouse from
[`sql/seed_test_data.sql`](sql/seed_test_data.sql), and puts the API on <http://localhost:8000>.
Skip to §2.4 if you use it.

### 2.2 Install the project

```bash
cd module-03-fastapi-azure/project-insight-api
python -m venv .venv
.venv\Scripts\activate            # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -e ".[dev]"
```

`-e` is an **editable** install: the package points at your source, so edits take effect without
reinstalling. `[dev]` adds pytest, httpx2 and ruff.

You need this even just to run the tests — the code lives in `src/`, and `pip install -e` is what
lets `from insight_api.main import app` resolve.

### 2.3 Run the API

```bash
uvicorn insight_api.main:app --reload
```

Expected output:

```
INFO:     Will watch for changes in these directories: ['.../project-insight-api']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
2026-09-08 21:14:02,881 INFO insight_api: Engine created for insight-api
INFO:     Application startup complete.
```

That `Engine created` line is your `lifespan` hook running — once, at startup.

### 2.4 Look at what it does

Open **<http://localhost:8000/docs>** and click "Try it out" on any endpoint. Nobody wrote that page;
it is generated from the function signatures.

| Endpoint | Answers |
|---|---|
| `GET /health` | Am I alive? (no dependencies) |
| `GET /health/ready` | Can I serve? (checks the database; **503** if not) |
| `GET /weather/cities` | Which cities have data, and over what period? |
| `GET /weather/daily` | Daily observations, filtered, sorted, paged |
| `GET /weather/weekly` | Weekly aggregates straight from `marts` |
| `GET /weather/cities/{city}/stats` | One city's summary; **404** if unknown |

From a terminal:

```bash
curl -s "http://localhost:8000/weather/cities"
curl -s "http://localhost:8000/weather/daily?city=De%20Bilt&limit=3"
curl -s "http://localhost:8000/weather/cities/De%20Bilt/stats"
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/weather/cities/Atlantis/stats"   # 404
```

### 2.5 The experiment worth doing

Stop the database while the API keeps running:

```bash
docker stop week2_postgres          # or insight_postgres
curl -s -o /dev/null -w "health:       %{http_code}\n" http://localhost:8000/health
curl -s -o /dev/null -w "health/ready: %{http_code}\n" http://localhost:8000/health/ready
docker start week2_postgres
```

`/health` stays **200**, `/health/ready` returns **503**. That is the design from Day 4: an
orchestrator should stop *routing* to this container, not *restart* it. Restarting wouldn't help —
the process is fine.

### 2.6 Run the tests

```bash
pytest -v
ruff check .
```

Expected: **25 passed, 6 skipped** without a database; **31 passed** with one.

The 6 skips are the integration tests, and they are the difference between "my contracts are tested"
and "my SQL has ever actually run". Watch that line.

---

## Part 3 — The big picture

### Architecture

```
                    HTTP request
                         │
                         ▼
              ┌──────────────────────┐
              │  main.py             │  lifespan: create the engine ONCE
              │  (FastAPI app)       │  include_router(...) x2
              └──────────┬───────────┘
                         │
        ┌────────────────┴─────────────────┐
        ▼                                  ▼
┌───────────────┐                 ┌──────────────────┐
│ routers/      │                 │ routers/         │
│  health.py    │                 │  weather.py      │
└───────┬───────┘                 └────────┬─────────┘
        │                                  │
        │        Depends(get_conn)         │  Depends(pagination)
        └──────────────┬───────────────────┘
                       ▼
              ┌──────────────────┐
              │ deps.py          │  borrow a pooled connection
              │                  │  validate limit/offset
              └────────┬─────────┘
                       │            config.py: Settings (env > .env > default)
                       ▼
              ┌──────────────────┐
              │ PostgreSQL       │  staging.weather_clean
              │                  │  marts.weather_weekly
              └────────┬─────────┘
                       │ rows (Decimal, date)
                       ▼
              ┌──────────────────┐
              │ models.py        │  response_model: filter, convert, validate, document
              └────────┬─────────┘
                       ▼
                   JSON response
```

### One request's journey — trace this, it's the whole project in miniature

`GET /weather/daily?city=Utrecht&limit=2&sort_by=temp&direction=asc`

1. **uvicorn** accepts the socket and hands FastAPI an ASGI request.
2. **Routing** matches `(GET, /weather/daily)` to `read_daily` — the row the `@router.get` decorator
   wrote at import time.
3. **The doorman** parses query parameters against the signature. `limit=2` becomes `int`; a
   `limit=abc` would stop here with a `422` and `read_daily` would never run.
4. **Dependencies resolve**, in order: `get_settings` (cached), then `pagination` (which caps `limit`
   at `max_page_size`), then `get_conn` — which borrows a connection from the pool and *pauses at its
   `yield`*.
5. **The handler runs.** `sort_by="temp"` is looked up in `SORTABLE_DAILY` → the column `temp_max_c`.
   A key that isn't in the map gets a `422`; a caller can never name a column.
6. **SQL executes** with `city` as a **bind parameter**. The SQL text and the value travel
   separately, so no value can become syntax.
7. **Postgres returns rows.** `temp_max_c` arrives as a Python `Decimal` (from `NUMERIC`), which
   `json.dumps` cannot serialise.
8. **`response_model=list[DailyObservationOut]`** converts each `Decimal` to a float and each `date`
   to `"2026-09-01"`, and **drops every column not declared**.
9. **Teardown**: `get_conn` resumes past its `yield` and returns the connection to the pool — even if
   step 5 had raised.
10. **uvicorn writes** `200 OK`, `Content-Type: application/json`, and the body.

Nine of those ten steps are things you never wrote code for. You wrote a *signature* and a *query*.

### Why the database has three layers, and which one we read

| Layer | Contents | This API |
|---|---|---|
| `raw` | JSONB exactly as the source sent it | **Never touched** |
| `staging` | Typed, cleaned daily rows | `/weather/daily`, `/weather/cities`, stats |
| `marts` | Pre-aggregated weekly answers | `/weather/weekly` |

Reading `raw` would mean re-implementing the staging SQL in Python, which then drifts away from the
SQL version. The layering exists so consumers don't have to care how the sausage is made.

---

## Part 4 — File by file

```
project-insight-api/
├── src/insight_api/
│   ├── config.py        Settings + get_settings()
│   ├── deps.py          get_conn, pagination
│   ├── models.py        response models (the plating standard)
│   ├── main.py          the app, lifespan, routers
│   └── routers/
│       ├── health.py    liveness + readiness
│       └── weather.py   the actual product
├── tests/
│   ├── conftest.py      the fake database
│   ├── test_health.py   unit
│   ├── test_weather.py  unit
│   └── test_db_integration.py   real SQL (skips without a database)
├── sql/seed_test_data.sql       a warehouse fixture for CI
├── docker/docker-compose.yml    API + its own Postgres
├── Dockerfile           multi-stage, non-root
├── .dockerignore        keeps .env and .venv out of the image
├── pyproject.toml       dependencies, pytest and ruff config
└── .github/workflows/
    ├── ci.yml           the bouncer  (lint + unit + integration)
    └── cd.yml           the delivery driver (build + deploy on merge)
```

### 1. `config.py` — settings in one place, validated

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg2://student:student123@localhost:5432/week2_db"
    default_page_size: int = 50
    max_page_size: int = 500
```

Module 2's `config.py` read `os.environ.get(...)` directly. This is the same idea with three
upgrades: values are **typed** (so `DEFAULT_PAGE_SIZE=fifty` fails at startup, not at 3 a.m.), a
`.env` file works automatically, and **environment beats `.env` beats default** — which is exactly
how one image runs on your laptop, in CI, and in Azure unchanged.

`@lru_cache` on `get_settings()` means the file is read once, not per request.

### 2. `deps.py` — the things handlers ask for

`get_conn` borrows one pooled connection per request:

```python
def get_conn(request: Request) -> Iterator[Connection]:
    engine = request.app.state.engine
    with engine.connect() as conn:
        yield conn
```

The `with` provides the try/finally, so the connection returns to the pool even when a handler
raises. Leak connections and the API works for an hour and then hangs forever.

`pagination` turns `?limit=&offset=` into a validated object and enforces `max_page_size` in **one
place** for every list endpoint.

**Everything in this file exists to create a seam.** Because handlers *ask*, `tests/conftest.py` can
swap in a fake with one dictionary entry.

### 3. `models.py` — the plating standard

Every response model sets `from_attributes=True` so it can read SQLAlchemy rows directly, and
declares `float` for `NUMERIC` columns so `Decimal` conversion happens at the boundary.

The important property is what's **absent**: any column added to the database later cannot appear in
a response, because it isn't declared. Allow-lists fail closed.

### 4. `main.py` — assembly

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_engine(settings.database_url, pool_pre_ping=True, ...)
    yield
    app.state.engine.dispose()
```

The engine is created **once per application**, not per request and not at import. Not at import
matters: the unit tests import this module, and importing must not require a database.

`pool_pre_ping=True` tests a pooled connection before handing it out — microseconds, and it prevents
the classic "server closed the connection unexpectedly" after an idle period.

### 5. `routers/health.py` — two questions, two endpoints

`/health` touches nothing. `/health/ready` runs `SELECT 1` and returns **503** on failure. Azure
uses these on Day 8 to decide whether to restart a container or merely stop routing to it.

### 6. `routers/weather.py` — the product

Two safety patterns you should be able to recite:

**Values are bound.** `WHERE city = :city` with `{"city": city}` — the value can never become syntax.

**Identifiers come from an allow-list.** Columns can't be bound, so:

```python
SORTABLE_DAILY = {"date": "obs_date", "temp": "temp_max_c", ...}
column = SORTABLE_DAILY.get(sort_by)      # caller gives a KEY; we supply the COLUMN
if column is None:
    raise HTTPException(422, ...)
```

The f-string that builds `ORDER BY {column}` is safe because every value it can contain was written
by us. Note `sort_by=obs_date` is rejected *even though that's a real column* — the vocabulary is
ours, not theirs.

**All handlers are `def`, not `async def`.** psycopg2 is a blocking driver, so FastAPI runs these in
a threadpool where blocking is safe. Making them `async def` would freeze the event loop for every
request in the service (Day 6). This is a deliberate, correct choice.

### 7. `tests/conftest.py` — the cardboard prep station

`FakeConnection` answers from canned rows and records what it was asked. The `client` fixture
installs it and — crucially — **clears the override in teardown**, so it can't leak into another test
and create a failure that depends on test order.

### 8. `.github/workflows/` — the robots

`ci.yml` has **two jobs on purpose**: `unit` (fast, no services) and `integration` (a real Postgres
service container, seeded from `sql/seed_test_data.sql`). It ends with a step that **fails the build
if the integration tests skipped** — otherwise the suite could stay green forever while never
executing a line of SQL.

`cd.yml` logs in with **OIDC** (no stored password), builds with `az acr build` (in the cloud, so no
Docker on the runner), tags with `${{ github.sha }}`, deploys, and smoke-tests the live URL with
retries for cold starts. `needs: test` means a red build can never deploy.

---

## Part 5 — Why it's designed this way

| Decision | Alternative | Why this one |
|---|---|---|
| Read-only API | Full CRUD | The warehouse is written by the Module 2 pipeline. Two writers means two sources of truth |
| `def` handlers | `async def` everywhere | psycopg2 blocks. `async def` + blocking = frozen event loop |
| Raw SQL via SQLAlchemy Core | An ORM | You just learned SQL. The queries stay readable and reviewable, and the layered SQL is the point |
| `response_model` on everything | Return dicts | Filters, converts, validates and documents — four jobs, one declaration |
| Router per domain | One `main.py` | Failures are readable, and it scales past ten endpoints |
| Engine in `lifespan` | Module-level `create_engine` | Importing the app must not require a database, or you can't unit test |
| `pool_size=5, overflow=5` | Defaults | Every replica gets its own pool; Postgres caps total connections at ~100 |
| One worker per container | `--workers 4` | Scale by adding containers. Keeps the connection arithmetic simple |
| `min-replicas 0` | Always warm | Free when idle. A cold start is fine for a portfolio demo |
| Commit SHA image tags | `:latest` | Reproducible, rollback-able, and `:latest` won't reliably redeploy |
| OIDC | A stored service-principal secret | No long-lived credential to leak or rotate |

---

## Part 6 — The recipe: build an API like this over ANY database

Transferable to your next project, and to interviews.

1. **Decide the questions**, not the tables. "What was the weather in Utrecht last week?" — then work
   backwards to endpoints. `/weather/daily?city=...` names a *thing*, with *options*.
2. **Write the response models first.** They are the contract. Deciding what leaves forces you to
   decide what the service is for.
3. **Make configuration a `BaseSettings` model.** Environment beats `.env` beats default. One
   artifact, many environments.
4. **Create the engine in `lifespan`, hand out connections with a `yield` dependency.** This one
   choice is what makes the whole thing testable.
5. **Bind every value. Allow-list every identifier.** No exceptions.
6. **Two health endpoints**, liveness dependency-free.
7. **Unit tests with overridden dependencies, integration tests that skip politely** — plus a CI job
   that fails if they *do* skip.
8. **Containerise:** dependencies before source, non-root, exec-form `CMD`, `--host 0.0.0.0`.
9. **CI as the gate, CD with `needs:`.** Tag with the commit SHA.
10. **Script the teardown** and use it.

### Worked variation: an API over the CBS statistics data

Swap the Module 2 source for CBS (Dutch statistics bureau) and almost nothing changes:

- `sql/` gains a mart like `marts.population_by_region`
- `models.py` gains `RegionStatsOut`
- `routers/statistics.py` mirrors `weather.py` with its own `SORTABLE` map
- Everything in `config.py`, `deps.py`, `main.py`, the Dockerfile and both workflows is **unchanged**

That's the sign the structure is right: adding a domain touches only the domain's files.

---

## Part 7 — Milestones (your Days 9–10)

### Milestone 1 — Run and trace (~45 min)

1. Get a database (§2.1), install (§2.2), run (§2.3).
2. Open `/docs`, exercise every endpoint.
3. Do the database-down experiment (§2.5).
4. **Trace one request** through the ten steps in Part 3 with the file open beside you. Write down,
   in your own words, what happens at step 8 and why it matters.

<details>
<summary>💡 What step 8 should say</summary>

`response_model` takes the raw database row and does four things: drops any column not declared,
converts `Decimal` → number and `date` → ISO string, validates that our own output matches what we
promised, and publishes the shape into `/docs`. Without it, `Decimal` would raise a `TypeError` on
serialisation and any new column would be published to the internet automatically.
</details>

### Milestone 2 — Prove the boundary holds (~20 min)

Without changing any handler, prove two things:

1. A malicious `city` value cannot execute SQL.
2. A new database column does not leak into responses.

<details>
<summary>💡 How</summary>

**1.** Ask for a city named `'; DROP SCHEMA staging CASCADE; --`:

```bash
curl -s "http://localhost:8000/weather/daily?city=%27%3B%20DROP%20SCHEMA%20staging%20CASCADE%3B%20--"
```

You get `[]` and your schema still exists — the string was treated as a city *name*, because it
travelled as a bind parameter.

**2.** Add a column and refill it, then call the endpoint:

```sql
ALTER TABLE staging.weather_clean ADD COLUMN internal_note TEXT DEFAULT 'do not publish';
```

```bash
curl -s "http://localhost:8000/weather/daily?limit=1"
```

`internal_note` is absent, because `DailyObservationOut` doesn't declare it. Clean up with
`ALTER TABLE staging.weather_clean DROP COLUMN internal_note;`.
</details>

### Milestone 3 — Add an endpoint (~1.5 h)

Add `GET /weather/records` returning, for each city: the hottest day ever recorded, the wettest day,
and the observation count. Include a `response_model`, paging, and a **404** when a `city` filter
matches nothing.

<details>
<summary>💡 Hints</summary>

- Add `CityRecordOut` to `models.py` with `from_attributes=True`.
- `DISTINCT ON (city)` is the Postgres-idiomatic "top row per group"; a window function
  (`ROW_NUMBER() OVER (PARTITION BY city ORDER BY temp_max_c DESC)`) also works — that's Module 2
  Day 4 material.
- Put the route in `weather.py` **above** any parameterised route it could collide with.
- Filters go in the query string; the resource is "records".
</details>

<details>
<summary>💡 Solution sketch</summary>

```python
class CityRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    city: str
    hottest_day: date | None
    hottest_temp_c: float | None
    wettest_day: date | None
    wettest_precip_mm: float | None
    days_observed: int

@router.get("/records", response_model=list[CityRecordOut], summary="Per-city records")
def read_records(
    city: str | None = Query(default=None),
    page: Pagination = Depends(pagination),
    conn: Connection = Depends(get_conn),
) -> list:
    clause = "WHERE city = :city" if city is not None else ""
    params: dict = {"limit": page.limit, "offset": page.offset}
    if city is not None:
        params["city"] = city

    rows = conn.execute(text(f"""
        WITH base AS (SELECT * FROM staging.weather_clean {clause}),
        hottest AS (
            SELECT DISTINCT ON (city) city, obs_date AS hottest_day, temp_max_c AS hottest_temp_c
            FROM base WHERE temp_max_c IS NOT NULL
            ORDER BY city, temp_max_c DESC, obs_date ASC
        ),
        wettest AS (
            SELECT DISTINCT ON (city) city, obs_date AS wettest_day, precip_mm AS wettest_precip_mm
            FROM base WHERE precip_mm IS NOT NULL
            ORDER BY city, precip_mm DESC, obs_date ASC
        ),
        counts AS (SELECT city, count(*) AS days_observed FROM base GROUP BY city)
        SELECT c.city, h.hottest_day, h.hottest_temp_c,
               w.wettest_day, w.wettest_precip_mm, c.days_observed
        FROM counts c
        LEFT JOIN hottest h ON h.city = c.city
        LEFT JOIN wettest w ON w.city = c.city
        ORDER BY c.city
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    if city is not None and not rows:
        raise HTTPException(404, detail=f"No observations for city {city!r}")
    return rows
```

Note the tie-breakers (`obs_date ASC`) in both `DISTINCT ON` clauses. Without them, two days with the
same temperature return an arbitrary winner — and your tests become flaky for reasons that take an
afternoon to find.
</details>

### Milestone 4 — Test your endpoint (~45 min)

Write, in `tests/test_weather.py`: a happy path, a 404, an exact-key-set assertion, and a
`parametrize`d paging-bounds test. Add one integration test in `test_db_integration.py` that runs the
real SQL. Get `pytest -v` and `ruff check .` green.

<details>
<summary>💡 Solution sketch</summary>

```python
def test_records_happy_path(client):
    r = client.get("/weather/records")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_records_unknown_city_is_404(client):
    assert client.get("/weather/records", params={"city": "Atlantis"}).status_code == 404

def test_records_shape_is_the_contract(client):
    row = client.get("/weather/records").json()[0]
    assert set(row) == {"city", "hottest_day", "hottest_temp_c",
                        "wettest_day", "wettest_precip_mm", "days_observed"}

@pytest.mark.parametrize(("params", "expected"), [
    ({"limit": 0}, 422), ({"limit": -1}, 422), ({"offset": -1}, 422), ({"limit": 1}, 200),
])
def test_records_paging_bounds(client, params, expected):
    assert client.get("/weather/records", params=params).status_code == expected
```

You'll need to teach the fake in `conftest.py` about the new query — add a branch keyed on
`"WITH base AS"` plus `"hottest"`, returning canned record rows.

The integration version:

```python
def test_records_runs_real_sql(live_client):
    r = live_client.get("/weather/records", params={"limit": 5})
    assert r.status_code == 200
    for row in r.json():
        assert row["days_observed"] >= 1
```

That last one is the important one. The unit tests never touch Postgres, so a typo in a column name
survives them all.
</details>

### Milestone 5 — Containerise (~30 min)

Build the image, run it against your database, and confirm three things: it answers on port 8000, it
runs as a non-root user, and `/health/ready` reports the database honestly.

<details>
<summary>💡 Commands</summary>

```bash
docker build -t insight-api:dev .
docker images insight-api:dev                       # note the size

# Linux: add --add-host=host.docker.internal:host-gateway
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql+psycopg2://student:student123@host.docker.internal:5432/week2_db" \
  insight-api:dev

curl -s http://localhost:8000/health/ready
docker run --rm insight-api:dev id                  # expect uid=1000(appuser)
```

If `/health/ready` returns 503 from inside the container but works on your host, the container can't
see your database — that's the `localhost`-means-the-container problem from Day 7. Use
`host.docker.internal`, or run the whole stack with `docker compose`.
</details>

### Milestone 6 — Publish and deploy (~1.5 h)

1. Copy this folder out to its own public GitHub repo (see
   [docs/GIT_GITHUB_GUIDE.md](../../docs/GIT_GITHUB_GUIDE.md)).
2. Watch `ci.yml` run. Get it **green**, both jobs.
3. Add the CI badge to `README.md`:
   `![CI](https://github.com/<you>/<repo>/actions/workflows/ci.yml/badge.svg)`
4. Work through [docs/AZURE_SETUP_GUIDE.md](../../docs/AZURE_SETUP_GUIDE.md): account, **budget
   alert**, CLI, OIDC federated credential (mind the immutable `subject` format), GitHub secrets and
   variables.
5. Deploy by hand once (Day 8 §4), confirm the public URL serves `/docs`.
6. Push a trivial change to `main` and watch `cd.yml` deploy it by itself.
7. Put the live URL in your README.
8. **Tear it down** when you're done: `az group delete --name rg-insight-api --yes --no-wait`.

### Stretch goals

- **Response caching** with an `ETag` or `Cache-Control` header on `/weather/weekly` (it changes once
  a day, so caching is nearly free).
- **API key auth** with a `Depends` that checks a header, returning `401` when absent and `403` when
  wrong — the distinction from Day 1.
- **Rate limiting** returning `429`.
- **A `/metrics` endpoint** counting requests per endpoint (a taste of Module 7's observability).
- **An async endpoint that actually earns it**: fan out to the live Open-Meteo API with
  `httpx2.AsyncClient` and `asyncio.gather`, comparing forecast against your stored history.

---

## Part 8 — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: insight_api` | Package not installed | `pip install -e ".[dev]"` from this folder |
| `AttributeError: 'State' object has no attribute 'engine'` | `TestClient` used without `with`, so `lifespan` never ran | `with TestClient(app) as client:` |
| `/health/ready` returns 503 | Database unreachable | `docker ps`; check `DATABASE_URL`; from a container use `host.docker.internal` |
| All 6 integration tests skip | No database with `staging.weather_clean` | Start the stack and run the pipeline, or use this project's compose |
| `TypeError: Object of type Decimal is not JSON serializable` | An endpoint without a `response_model` | Declare one, with `float` for `NUMERIC` columns |
| `422` on a request you think is valid | The doorman rejected a value | Read `detail[].loc` — it names the exact field |
| A new route returns another handler's response | Route order | Specific routes above parameterised ones |
| `ruff` flags `B008` on `Depends(...)` | Bugbear doesn't know FastAPI | Already handled: `extend-immutable-calls` in `pyproject.toml` |
| Container runs, curl gets nothing | uvicorn bound to `127.0.0.1` | `--host 0.0.0.0` |
| Compose serves Module 2's data, not the seed | Compose names the project after the compose file's **parent directory** — `docker` in both modules — so the stacks shared a volume | Fixed by `name: insight-api` in `docker/docker-compose.yml`. **Never run `down -v` in a stack without an explicit `name:`** — it can delete another project's database |
| Seed changes don't take effect | Postgres only runs `/docker-entrypoint-initdb.d/` on an **empty** data directory | `docker compose -f docker/docker-compose.yml down -v`, then `up` again |
| Slow rebuilds on every code edit | `COPY . .` before `pip install` | Dependencies before source |
| Azure: `AADSTS70021` | Federated credential `subject` mismatch | Regenerate it — new repos need `owner@id/repo@id` |
| Azure: deploy succeeds, old code serves | Reused image tag | Tag with the commit SHA |
| Unexpected Azure bill | ACR Basic bills ~$0.17/day always | `az group delete`, then check Cost Analysis |

---

## ✅ Definition of done

- [ ] `uvicorn insight_api.main:app --reload` serves `/docs`
- [ ] `pytest -v` green, **with the integration tests running rather than skipping**
- [ ] `ruff check .` clean
- [ ] You added an endpoint (Milestone 3) with tests (Milestone 4)
- [ ] `docker build` works and the container runs as a non-root user
- [ ] Published as your own public repo with a **green CI badge**
- [ ] Deployed to Azure, public URL in the README, then torn down
- [ ] You can explain, out loud: why handlers are `def`, why values are bound and identifiers
      allow-listed, and why `needs: test` is in `cd.yml`

Then report **"Module 3 done"** so [PLAN.md](../../PLAN.md) gets updated — and ask for **Module 4**.
