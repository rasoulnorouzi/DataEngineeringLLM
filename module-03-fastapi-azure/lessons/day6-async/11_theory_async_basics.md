# Day 6 — Async: One Waiter, Many Tables

**Time:** ~2 h · **Prerequisite:** Days 2–5

Week A built the API. Week B ships it. First, the thing that decides whether your service handles
ten users or ten thousand — and the mistake that makes `async` *slower* than not using it at all.

---

## 🧠 Before you read — predict first

1. A waiter takes an order, walks it to the kitchen, and then **stands there watching the chef cook**
   until the dish is ready. What's wrong, and what should they do instead?
2. Your endpoint spends 200 ms waiting for the database. During those 200 ms, is your CPU busy?
3. If `async def` is the fast one, why would a framework ever let you write a plain `def` handler?

---

## 1. The problem async actually solves

A typical request spends its life like this:

```
receive request   0.1 ms   CPU busy
parse & validate  0.2 ms   CPU busy
query database  200.0 ms   CPU IDLE - just waiting for another computer
format response   0.3 ms   CPU busy
```

**99.7% of that request is waiting.** Prediction question 2: your CPU is doing nothing at all for
200 milliseconds. It could have served hundreds of other requests in that time.

Work that waits on something external — a database, an HTTP call, a disk — is called **I/O-bound**.
Work that actually computes — resizing an image, training a model — is **CPU-bound**. Async helps
enormously with the first and not at all with the second.

### The restaurant, again

**Synchronous waiter:** takes table 1's order, carries it to the kitchen, stands at the pass
watching the chef, carries the dish back, *then* goes to table 2. Tables 2 through 10 wait, staring
at an idle waiter who is technically "busy".

**Asynchronous waiter:** takes table 1's order, hands it to the kitchen, and *immediately* goes to
table 2. When the kitchen rings a bell, they collect whatever is ready. One waiter, ten tables, and
nobody is standing still.

The chef didn't get faster. The kitchen has the same capacity. The waiter simply **stopped
blocking** — and that alone multiplied the tables served.

> 🎯 **Remember this** — async doesn't make anything faster. It stops you **waiting idly**. One
> waiter, many tables.

### Concurrency is not parallelism

| | Concurrency | Parallelism |
|---|---|---|
| Meaning | Many tasks *in progress* | Many tasks *executing at once* |
| Restaurant | One waiter, ten tables | Ten waiters |
| Needs | One thread | Multiple cores |
| Helps with | **I/O-bound** work | **CPU-bound** work |
| In Python | `asyncio` | multiple processes |

Async gives you **concurrency**, on **one** thread. That single thread is called the **event loop**:
a scheduler that keeps a list of paused tasks and resumes each one when the thing it was waiting for
is ready.

---

## 2. `async def` and `await`, token by token

```python
import httpx

async def fetch_weather(city: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/weather?city={city}")
    return response.json()
```

| Token | Meaning |
|---|---|
| `async def` | Defines a **coroutine function**. Calling it returns a coroutine; it does **not** run |
| `await` | "Pause me here and let the loop run something else until this finishes" |
| `async with` | A context manager whose setup/teardown may themselves await |
| `response.json()` | No `await` — parsing is CPU work, not waiting |

Two rules with no exceptions:

1. **`await` is only legal inside `async def`.** At module level or in a plain `def` it's a
   `SyntaxError`.
2. **A coroutine does nothing until awaited.** `fetch_weather("Utrecht")` on its own creates an
   object and returns immediately. Forgetting `await` is the most common async bug in Python, and
   the symptom is a function that "does nothing" while your linter warns about a never-awaited
   coroutine.

`await` is not "wait for this". It is closer to **"I'm going to be a while — go do something else
and come back to me."** That is precisely the waiter handing the order to the kitchen.

### Doing several things at once: `asyncio.gather`

```python
import asyncio

async def fetch_all(cities: list[str]) -> list[dict]:
    results = await asyncio.gather(*(fetch_weather(c) for c in cities))
    return list(results)
```

| Token | Meaning |
|---|---|
| `asyncio.gather(a, b, c)` | Start all of them, wait for all to finish, return results **in order** |
| `*( ... )` | Unpacks the generator into separate arguments |

Six cities at 200 ms each: sequentially 1.2 s, gathered ≈ **200 ms**. Same requests, same network,
same server. You simply stopped queuing.

Your Module 2 `fetch_all` looped over cities with `time.sleep(0.5)` between them, deliberately, to
be polite to a free public API. That was the right call there — a nightly batch has no user waiting.
In a web request, where someone is watching a spinner, `gather` is the right call. **The same code
shape is correct in one context and wrong in the other**, which is why "always use async" is bad
advice.

> 🎯 **Remember this** — `async def` defines it, `await` pauses it, `gather` runs several at once.
> A coroutine you forgot to `await` does nothing at all.

### 🔁 Recall check

<details>
<summary>What does this print, and why?</summary>

```python
async def get_temp():
    await asyncio.sleep(1)
    return 21.4

async def main():
    temp = get_temp()
    print(temp)
```

```
<coroutine object get_temp at 0x7f...>
```

`get_temp()` was **called but never awaited**, so it created a coroutine object and did nothing
else. `await get_temp()` gives you `21.4`. Python also emits `RuntimeWarning: coroutine 'get_temp'
was never awaited` — worth learning to spot, because it's usually the whole bug.
</details>

---

## 3. The rule that matters most in FastAPI

FastAPI accepts both kinds of handler:

```python
@app.get("/a")
def sync_handler(): ...          # plain def

@app.get("/b")
async def async_handler(): ...   # async def
```

They are **not** "slow" and "fast". They are routed completely differently, and this is the single
most valuable thing on today's page:

| You write | FastAPI runs it | Blocking code inside is |
|---|---|---|
| `def` | In a **threadpool**, off the event loop | ✅ **Fine** — it blocks one worker thread |
| `async def` | **Directly on the event loop** | 🚨 **Catastrophic** — it blocks *every* request |

So:

```python
# ✅ CORRECT. psycopg2 is blocking, so use a plain def.
@app.get("/weather")
def read_weather(conn = Depends(get_conn)):
    return conn.execute(text("SELECT ...")).mappings().all()

# 🚨 DISASTER. Blocking driver called on the event loop.
@app.get("/weather")
async def read_weather(conn = Depends(get_conn)):
    return conn.execute(text("SELECT ...")).mappings().all()    # no await - it BLOCKS
```

The second one has no `await` in it. There is nothing to yield control at, so for the entire 200 ms
of that query **the event loop is frozen** — no other request is served, health checks time out, and
the whole service stalls. One user's slow query becomes everyone's outage.

The cruel part is that it looks fine in development. With one user there's nothing else for the loop
to do. It fails only under load, in production, which is where you least want to discover it.

### The rule, in one line

> **If you're not `await`ing anything, use plain `def`.**

Say it out loud once. It resolves prediction question 3 completely: `def` isn't a legacy fallback,
it's the *correct* choice for blocking libraries — and FastAPI's threadpool makes it safe.

Which library is which:

| Library | Kind | Handler to use |
|---|---|---|
| `psycopg2`, `SQLAlchemy` (default) | blocking | `def` |
| `requests` | blocking | `def` |
| `time.sleep` | blocking | `def` (or `asyncio.sleep` in async) |
| `httpx.AsyncClient` | async | `async def` + `await` |
| `asyncpg`, SQLAlchemy async engine | async | `async def` + `await` |
| Pure computation, dict/list work | neither | `def` |

**This module's project uses `def` handlers throughout**, because it talks to Postgres through
psycopg2, which is blocking. That is a deliberate, correct choice — not a shortcut. Module 5's RAG
service will call HTTP APIs with `httpx.AsyncClient`, and there `async def` will earn its place.

> 🎯 **Remember this** — `def` → threadpool, safe for blocking. `async def` → event loop, only for
> `await`. **Blocking code in `async def` freezes the whole service.**

### 🔁 Recall check

<details>
<summary>Which of these four is dangerous, and what exactly happens?</summary>

```python
@app.get("/1")
def a(): time.sleep(1); return {}

@app.get("/2")
async def b(): await asyncio.sleep(1); return {}

@app.get("/3")
async def c(): time.sleep(1); return {}

@app.get("/4")
def d(): return requests.get("https://slow.example.com").json()
```

**`/3` is the dangerous one.** `time.sleep` is blocking and it is being called directly on the event
loop, with no `await` to yield control. For that full second **every** request to **every** endpoint
is frozen.

- `/1` — fine. Blocking, but in a threadpool: it occupies one worker, others keep serving.
- `/2` — fine and ideal. `asyncio.sleep` is the async version, so the loop is free during the wait.
- `/4` — fine. Same reasoning as `/1`; `requests` is blocking, and a plain `def` is the right home
  for it.

Note the symmetry: `/1` and `/3` contain the *identical line*. The keyword on the line above is the
entire difference between "fine" and "outage".
</details>

---

## 4. Async dependencies

The same rule, one level down:

```python
def get_conn(request: Request):                # blocking driver -> plain def
    with request.app.state.engine.connect() as conn:
        yield conn

async def get_http_client():                   # async library -> async def
    async with httpx.AsyncClient(timeout=10) as client:
        yield client
```

FastAPI runs `def` dependencies in the threadpool too, so a blocking dependency is safe. And the
mixing rules are generous:

- An `async def` handler **may** depend on a `def` dependency. ✅
- A `def` handler **may** depend on an `async def` dependency. ✅

You don't need to convert everything at once. Choose per function, based on what that function
actually does.

---

## 5. Timeouts: the part everyone forgets

Async lets one process hold thousands of open waits. Without timeouts, that's a liability rather
than a feature: a hung upstream server can accumulate paused tasks until you run out of memory.

```python
async with httpx.AsyncClient(timeout=10.0) as client:      # seconds, applies to every request
    r = await client.get(url)
```

`httpx.AsyncClient()` with no argument uses a 5-second default; `timeout=None` disables it, which is
almost always a mistake. Your Module 2 `fetch.py` passed `timeout=30` to `requests.get` for exactly
this reason.

Rule of thumb: **every call that leaves your process gets a timeout.** Databases, HTTP APIs,
message queues. A slow dependency should degrade your service, not hang it forever.

> 🎯 **Remember this** — every outbound call gets a timeout. Async makes hangs cheaper to
> accumulate, which makes them easier to ignore until you fall over.

---

## 6. Workers: the other axis

Async gives concurrency on one core. To use the machine's other cores you need **processes**:

```bash
uvicorn main:app --workers 4
```

Each worker is a separate Python process with its own event loop, its own memory, and — note this —
**its own database connection pool**. Day 4's arithmetic returns: `pool_size 5 + max_overflow 10`
per worker × 4 workers = up to **60 connections** from one container. Postgres defaults to 100 total.
Two containers like that and you're locked out with "too many connections".

A rough starting point is `(2 × cores) + 1` workers, then measure. On Azure Container Apps (Day 8)
you'll typically run **1 worker per container** and let the platform scale by adding containers
instead — simpler to reason about, and each container's pool stays small and predictable.

---

## 🔁 Spaced review

<details>
<summary>1. (Day 4) Your <code>async def</code> handler calls a <code>def</code> dependency that opens a psycopg2 connection. Is the event loop blocked?</summary>

**No.** FastAPI runs `def` dependencies in the threadpool, just like `def` handlers. The blocking
connect happens on a worker thread and the loop stays free.

This is why the mixing rules are safe: FastAPI looks at each function's own definition and routes it
accordingly. The danger is only ever blocking code written *directly inside* an `async def`.
</details>

<details>
<summary>2. (Day 5) You add <code>async def</code> handlers. Do your <code>TestClient</code> tests need changing?</summary>

**No.** `TestClient` runs an event loop internally, so your tests remain ordinary synchronous
functions. You'd only need `httpx.AsyncClient` with `ASGITransport` if the *test body itself* had to
await something.
</details>

<details>
<summary>3. (Module 2) Your pipeline sleeps 0.5 s between city fetches. Would <code>asyncio.gather</code> be an improvement there?</summary>

**No** — and this is the point of the day. The sleep is deliberate politeness to a free public API,
and the pipeline is a nightly batch with no user waiting on it. Making it six times faster gains
nothing and risks being rate-limited or blocked.

`gather` is right when **someone is waiting**. Context decides, not the keyword.
</details>

---

## 📌 Day 6 on one screen

```
WHY          I/O-bound work is 99% waiting. Async stops the waiting being idle.
             One waiter, many tables. Concurrency (1 thread), not parallelism (many cores).

SYNTAX       async def  -> defines a coroutine (does NOT run it)
             await      -> "pause me, run something else"
             gather()   -> start many, wait for all
             forgot await? -> you get a coroutine object and silence

THE RULE     def        -> threadpool. Blocking code is SAFE here.
             async def  -> event loop. Blocking code FREEZES EVERYTHING.
             >>> If you're not awaiting anything, use plain def. <<<

THIS PROJECT psycopg2 is blocking -> def handlers. Correct, not lazy.

ALWAYS       timeout on every outbound call
             workers x pool_size must stay under Postgres max_connections
```

---

## ➡️ Next

Notebook **[12_async_practice.ipynb](12_async_practice.ipynb)** — measure sequential vs gathered
calls with a stopwatch, then reproduce the blocked-event-loop disaster yourself and watch a second
request wait behind the first.

Day 7 puts the app in a **container**.
