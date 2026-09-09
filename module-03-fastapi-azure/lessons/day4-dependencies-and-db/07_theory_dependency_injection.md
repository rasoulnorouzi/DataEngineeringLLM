# Day 4 — Dependency Injection & Talking to Your Database

**Time:** ~2.5 h · **Prerequisite:** Days 2–3, and a running Module 2 Postgres

Your API has a shape. It has no data. Today you connect it to the weather database you built in
Module 2 — and you do it in the one way that makes Day 5's tests easy instead of miserable.

---

## 🧠 Before you read — predict first

1. Every endpoint needs a database connection. What's wrong with `engine = create_engine(URL)` at
   the top of the file and using it everywhere?
2. A database connection must be **closed**, even when the handler crashes halfway through. Where
   would you put that cleanup?
3. Tomorrow you'll test these endpoints without a database running. What would have to be true about
   today's code for that to be possible?

---

## 1. Dependency injection, minus the jargon

The phrase sounds like enterprise Java. The idea takes one sentence:

> **Don't build what you need. Ask for it.**

The restaurant version: the waiter doesn't grow vegetables. They ask the prep station for what the
dish needs. Swap in a different prep station — a smaller one, a rehearsal one made of cardboard —
and the waiter's script doesn't change a word.

In code:

```python
# ❌ the handler BUILDS its dependency
@app.get("/weather")
def read_weather():
    engine = create_engine(DATABASE_URL)     # hard-wired to the real database
    with engine.connect() as conn:
        ...
```

```python
# ✅ the handler ASKS for its dependency
@app.get("/weather")
def read_weather(conn = Depends(get_conn)):  # "someone hand me a connection"
    ...
```

Four things improve at once, and the fourth is the one that pays the rent:

| | Building it | Asking for it |
|---|---|---|
| Connection reuse | New engine per request — slow | One shared pool |
| Cleanup | You write `close()` in every handler | Written once |
| Duplication | Copied into 20 handlers | One function |
| **Testing** | **Impossible without a real database** | **Swap in a fake, one line** |

That last row is prediction question 3, answered in advance. Testability is not a side effect of
dependency injection — it is the reason to do it.

> 🎯 **Remember this** — dependency injection is just *"ask, don't build."* The waiter doesn't grow
> the vegetables.

---

## 2. `Depends`, token by token

```python
from fastapi import Depends

def get_settings():
    return {"env": "dev"}

@app.get("/info")
def read_info(settings = Depends(get_settings)):
    return settings
```

| Token | Meaning |
|---|---|
| `get_settings` | An ordinary function. Nothing special about it |
| `Depends(get_settings)` | **No parentheses on `get_settings`.** You pass the function itself, not its result |
| `settings = ...` | Before calling your handler, FastAPI calls `get_settings()` and passes the result here |

The missing parentheses are the number-one beginner error. `Depends(get_settings())` calls the
function **once, at import time**, and hands FastAPI the return value — so your "dependency" is a
frozen dict computed at startup, and it silently never refreshes. Pass the **function object**;
FastAPI decides when to call it.

Dependencies get everything handlers get, including their own parameters:

```python
def pagination(limit: int = 10, offset: int = 0):
    return {"limit": min(limit, 100), "offset": offset}

@app.get("/cities")
def list_cities(page = Depends(pagination)): ...

@app.get("/weather")
def list_weather(page = Depends(pagination)): ...   # same rules, one definition
```

`limit` and `offset` are now real query parameters on **both** endpoints, documented in `/docs`,
validated by the doorman — and the capping rule lives in exactly one place. Change the maximum once
and every endpoint follows.

They also nest. A dependency can depend on a dependency:

```python
def get_settings(): ...
def get_engine(settings = Depends(get_settings)): ...
def get_conn(engine = Depends(get_engine)): ...

@app.get("/weather")
def read(conn = Depends(get_conn)): ...      # resolves the whole chain, in order
```

FastAPI walks the tree and caches each dependency **per request**, so `get_settings` runs once even
if three things need it.

> 🎯 **Remember this** — `Depends(func)`, never `Depends(func())`. Pass the recipe, not the meal.

### 🔁 Recall check

<details>
<summary>What actually goes wrong with <code>Depends(get_db())</code> — and why is it so hard to spot?</summary>

`get_db()` runs immediately, at import time, and its **return value** is passed to `Depends`. FastAPI
then treats that value as a callable to invoke per request, which either raises a confusing error or,
worse, works — handing every request the same object created once at startup.

It's hard to spot because in development, with one user and a connection that never times out, a
single shared session behaves fine. It fails under concurrency, after an idle timeout, or once a
transaction goes bad and poisons the shared session for every subsequent request. Classic
"works on my machine".
</details>

---

## 3. `yield` dependencies: setup and guaranteed teardown

Prediction question 2 was: where does cleanup go? Here.

```python
def get_conn():
    conn = engine.connect()      # setup - before the handler
    try:
        yield conn               # the handler runs, receiving conn
    finally:
        conn.close()             # teardown - ALWAYS, even if the handler raised
```

| Token | Meaning |
|---|---|
| `yield` (not `return`) | Makes this a generator. FastAPI pauses here and runs your handler |
| everything before `yield` | Setup |
| `try/finally` | `finally` runs even if the handler raises |
| everything after `yield` | Teardown, after the response is produced |

The order per request is: **setup → handler → teardown → response sent.**

This is the same shape as a `with` block, which you've used since Module 1:

```python
with open("f.txt") as f:     # setup
    ...                      # body
                             # teardown, guaranteed
```

A `yield` dependency is a `with` block whose body is your handler. If you understand `with`, you
already understand this.

Without `try/finally`, a handler that raises would skip the close and **leak a connection**. Leak
enough and the pool is exhausted; the symptom is an API that works for an hour and then hangs
forever, which is a genuinely horrible thing to debug. The four characters `try:` and `finally:` are
the whole fix.

> 🎯 **Remember this** — `yield` splits a dependency into setup / handler / teardown, and `finally`
> is what makes the teardown a promise rather than a hope.

---

## 4. Configuration: `pydantic-settings`

Your Module 2 pipeline read `os.environ.get("DATABASE_URL", "postgresql+...")` in `config.py`. That
works, but it's stringly-typed and silent when misconfigured. Since you now know Pydantic, use it on
your settings too.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://student:student123@localhost:5432/week2_db"
    app_name: str = "insight-api"
    default_page_size: int = 50
```

| Token | Meaning |
|---|---|
| `BaseSettings` | Like `BaseModel`, but fields are filled from **environment variables** |
| `env_file=".env"` | Also read a local `.env` file (git-ignored, as in Module 2) |
| `extra="ignore"` | Don't crash on unrelated environment variables. Your shell has hundreds |
| `database_url` | Matched **case-insensitively** to `DATABASE_URL` |
| `= "postgresql..."` | Default for local development |

Precedence, highest first: **real environment variable → `.env` file → default in the class.** That
ordering is what lets the same image run locally, in CI, and in Azure with nothing changed but the
environment — which is precisely how you'll deploy on Day 8.

Because it's a Pydantic model, `default_page_size: int` means a typo like `DEFAULT_PAGE_SIZE=fifty`
crashes **at startup with a clear message**, instead of at 3 a.m. inside a query.

Wrap it in a cached dependency:

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`@lru_cache` memoises: the first call builds `Settings` (reading the file and environment), every
later call returns the same object. Without it you'd re-read `.env` from disk on every request.

> 🎯 **Remember this** — settings are a Pydantic model too. Environment beats `.env` beats default.

---

## 5. Connecting to Postgres

You already met SQLAlchemy in Module 2's `load.py` and `transform.py`. Same library, same concepts.

### The engine is created **once**

```python
from sqlalchemy import create_engine

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
```

| Argument | Meaning |
|---|---|
| `pool_pre_ping=True` | Test a pooled connection with a tiny query before handing it out. Costs microseconds; prevents the classic "server closed the connection unexpectedly" after an idle period |
| `pool_size=5` | Connections kept open permanently |
| `max_overflow=10` | Extra connections allowed under load, closed afterwards. Ceiling here is 15 |

An **engine** is not a connection. It's a factory plus a **pool** of reusable connections. Creating
one is expensive (DNS, TCP, TLS, authentication); creating one per request would be the mistake in
prediction question 1. Create it once at startup, borrow from it per request.

Postgres has a hard limit on concurrent connections (100 by default) shared across everything that
talks to it. `pool_size + max_overflow`, times the number of running containers, must stay under it.
On Day 8 you'll scale to multiple replicas, and this multiplication is the thing that bites people.

### Startup and shutdown: `lifespan`

Where should that `create_engine` call live? Not at module import, because importing your app (which
your tests will do) would then require a database. Use the **lifespan** hook:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    yield                                  # <- the application runs here
    app.state.engine.dispose()             # shutdown: close every pooled connection

app = FastAPI(lifespan=lifespan)
```

| Token | Meaning |
|---|---|
| `@asynccontextmanager` | Turns the generator into an async `with`-style context manager |
| before `yield` | Runs **once at startup** |
| `yield` | The app serves requests for as long as this is suspended |
| after `yield` | Runs **once at shutdown** |
| `app.state` | A namespace on the app for exactly this kind of shared object |

Same setup/teardown shape as a `yield` dependency, one level up: per-application instead of
per-request. Two clocks, same pattern.

> ⚠️ You may find `@app.on_event("startup")` in tutorials. It is **deprecated**; `lifespan` replaced
> it. Another case where an old blog post will quietly teach you the wrong thing.

### The per-request connection dependency

```python
from fastapi import Request

def get_conn(request: Request):
    with request.app.state.engine.connect() as conn:
        yield conn
```

`request: Request` is FastAPI handing you the raw request object, which knows about `app`, which
holds the engine. The `with` block borrows a connection from the pool and returns it afterwards —
`with` provides the `try/finally` for you here.

### Querying safely

```python
from sqlalchemy import text

@app.get("/weather/daily")
def read_daily(city: str, limit: int = 50, conn = Depends(get_conn)):
    rows = conn.execute(
        text("""
            SELECT city, obs_date, temp_max_c, temp_min_c, precip_mm
            FROM staging.weather_clean
            WHERE city = :city
            ORDER BY obs_date DESC
            LIMIT :limit
        """),
        {"city": city, "limit": limit},
    ).mappings().all()
    return rows
```

Take this apart:

| Piece | Meaning |
|---|---|
| `text("...")` | Marks a raw SQL string. SQLAlchemy 2.0 refuses bare strings deliberately |
| `:city`, `:limit` | **Bind parameters** — placeholders, not string formatting |
| `{"city": city, ...}` | The values, sent to the database *separately from the SQL* |
| `.mappings()` | Yield each row as a dict-like object keyed by column name |
| `.all()` | Materialise all rows into a list |

### 🚨 Why bind parameters, not f-strings

```python
# ❌ NEVER. This is SQL injection.
conn.execute(text(f"SELECT * FROM weather WHERE city = '{city}'"))
```

If `city` is `'; DROP TABLE raw.weather_daily; --`, the database receives two statements and executes
both. Your evidence locker is gone.

With bind parameters the SQL and the data travel on **separate channels**. The database parses
`WHERE city = :city` first, then binds the value. A value can never become syntax, no matter what
characters it contains. It's also faster, because the parsed plan can be reused.

There is one thing you cannot parameterise: **identifiers**. Table names, column names and `ORDER BY`
directions are syntax, not data, so `ORDER BY :column` does not work. When those must vary, validate
against an allow-list you control:

```python
SORTABLE = {"date": "obs_date", "temp": "temp_max_c"}     # caller's word -> your column name
column = SORTABLE.get(sort_by)
if column is None:
    raise HTTPException(422, detail=f"sort_by must be one of {sorted(SORTABLE)}")
```

The caller never supplies a column name; they supply a **key**, and you supply the column. Same
allow-list-fails-closed principle as `response_model` on Day 3.

> 🎯 **Remember this** — values go in **bind parameters**, always. Identifiers can't be
> parameterised, so they go through an **allow-list**.

### 🔁 Recall check

<details>
<summary>Your endpoint takes <code>?sort=temp_max_c&direction=desc</code> and builds <code>f"ORDER BY {sort} {direction}"</code>. Is this exploitable, and how would you fix it?</summary>

**Yes.** `?sort=1;DROP SCHEMA raw CASCADE;--` is injected verbatim, because `ORDER BY` takes an
identifier and identifiers cannot be bound. Even without a destructive payload, an attacker can use
`ORDER BY (SELECT ...)` to read data your API never intended to expose.

Fix with two allow-lists and no string interpolation of caller input:

```python
SORTABLE = {"date": "obs_date", "temp": "temp_max_c"}
DIRECTIONS = {"asc": "ASC", "desc": "DESC"}

col = SORTABLE.get(sort)
dir_ = DIRECTIONS.get(direction, "ASC")
if col is None:
    raise HTTPException(422, detail=f"sort must be one of {sorted(SORTABLE)}")
sql = text(f"SELECT ... ORDER BY {col} {dir_} LIMIT :limit")   # both values are OURS
```

The f-string is now safe because every value it can contain was written by you.
</details>

---

## 6. Health checks that tell the truth

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

This endpoint answers "is the Python process alive?" — and nothing more. It returns `200` while the
database is on fire, so your monitoring is green during an outage. Azure will use this on Day 8 to
decide whether to send traffic to a container, so a lying health check has real consequences.

Two checks, two questions:

```python
@app.get("/health")                      # LIVENESS: am I alive? (no dependencies)
def health():
    return {"status": "ok"}

@app.get("/health/ready")                # READINESS: can I actually serve? (checks dependencies)
def readiness(conn = Depends(get_conn)):
    try:
        conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ready", "database": "ok"}
```

| | Liveness | Readiness |
|---|---|---|
| Question | Is the process alive? | Can it serve requests? |
| Checks dependencies | No | Yes |
| Failure means | **Restart me** | **Stop sending me traffic** |

Keep liveness dependency-free. If liveness checked the database, a brief database blip would make the
orchestrator restart every container — turning a small outage into a restart storm at the exact
moment the database is least able to cope.

And note the code: **`503`, not `500`**. The service is fine; a dependency isn't. That's precisely
the distinction Day 1 drew, now doing real work.

> 🎯 **Remember this** — liveness = *restart me*, readiness = *don't route to me*. Dependency down =
> `503`.

---

## 🔁 Spaced review

<details>
<summary>1. (Day 3) Your query returns a <code>Decimal</code> for <code>temp_max_c</code>. What stops that breaking JSON serialisation?</summary>

`response_model` with `temp_max_c: float`. Pydantic converts `Decimal` to a JSON number at the
boundary. Without it, `json.dumps` raises `TypeError: Object of type Decimal is not JSON
serializable` — a `500` for what is really a missing type declaration.
</details>

<details>
<summary>2. (Day 2) Which of these come from where: <code>/weather/{city}</code> with <code>def f(city: str, limit: int = 10, conn = Depends(get_conn))</code>?</summary>

`city` → path (it's in the route). `limit` → query (scalar, not in the path, has a default so
optional). `conn` → **neither** — `Depends` is the fourth source, and it never appears in the
OpenAPI schema because it isn't something the caller sends.
</details>

<details>
<summary>3. (Module 2) Which schema should the API read from, and which should it never touch?</summary>

Read from **`marts`** first (pre-aggregated, fast, stable), and `staging` when you need daily detail.
**Never `raw`.** Raw is the evidence locker: JSONB payloads in whatever shape the source sent them,
deliberately unprocessed. An API that reads raw re-implements your staging logic in Python and will
drift away from the SQL version.
</details>

---

## 📌 Day 4 on one screen

```python
# CONFIG (env > .env > default)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg2://..."

@lru_cache
def get_settings(): return Settings()

# ENGINE: once per APPLICATION
@asynccontextmanager
async def lifespan(app):
    app.state.engine = create_engine(url, pool_pre_ping=True)
    yield
    app.state.engine.dispose()

# CONNECTION: once per REQUEST
def get_conn(request: Request):
    with request.app.state.engine.connect() as conn:
        yield conn              # setup / handler / teardown

@app.get("/weather/daily")
def read(city: str, conn = Depends(get_conn)):     # Depends(func) NOT Depends(func())
    return conn.execute(
        text("SELECT ... WHERE city = :city"),     # BIND params for values
        {"city": city},
    ).mappings().all()
```

| | |
|---|---|
| DI in one line | ask, don't build |
| `Depends(f)` vs `Depends(f())` | recipe vs meal. Always the recipe |
| `yield` + `finally` | guaranteed teardown, even on exceptions |
| engine vs connection | per application vs per request |
| values vs identifiers | bind parameters vs allow-list |
| liveness vs readiness | restart me vs stop routing to me (`503`) |

---

## ➡️ Next

Notebook **[08_db_and_deps_practice.ipynb](08_db_and_deps_practice.ipynb)** — wire the API to your
Module 2 database, run real queries, and try the SQL injection yourself against a throwaway table so
you never forget why bind parameters exist.

Day 5 tests all of this **without a database**, by swapping the prep station for a cardboard one.
Today's `Depends` is what makes that a one-liner.
