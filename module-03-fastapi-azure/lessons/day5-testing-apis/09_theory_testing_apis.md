# Day 5 — Testing an API Without Running It

**Time:** ~2.5 h · **Prerequisite:** Day 4 (`Depends`), and Module 2 Day 8 (pytest, fixtures, CI)

In Module 2 you tested functions. Today you test **endpoints** — and you do it without starting a
server and without a database. Yesterday's dependency injection is what makes that possible.

---

## 🧠 Before you read — predict first

1. To test `GET /weather/daily`, do you have to start uvicorn, wait for it to boot, send a real
   request over the network, and shut it down?
2. Your handler asks for a database connection with `Depends(get_conn)`. How could a test give it a
   fake one *without editing the handler*?
3. Your test asserts `response.json() == {"city": "Utrecht", "temp_max_c": 21.4}`. Someone adds a
   harmless new field to the response. Should your test fail?

---

## 1. `TestClient`: a server without a server

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Prediction question 1: **no server, no network, no port.** `TestClient` calls your application
directly, in-process, through the same ASGI interface uvicorn uses. Your routing, validation,
dependencies, and response models all run exactly as in production. Only the socket is missing.

| Token | Meaning |
|---|---|
| `TestClient(app)` | Wraps your app object. Built on `httpx` |
| `client.get("/health")` | Looks like a network call. Is a direct function call |
| `response.status_code` | `int` |
| `response.json()` | Body, parsed |
| `response.text` | Body, unparsed |
| `response.headers` | Dict-like, case-insensitive |

The full range mirrors `requests`, which you already know from Module 2:

```python
client.get("/cities", params={"limit": 5})            # query string
client.post("/cities", json={"name": "Utrecht"})      # JSON body - note json=, not data=
client.put("/cities/Utrecht", json={...})
client.delete("/cities/Utrecht")
client.get("/admin", headers={"X-Token": "secret"})
```

`json=` serialises the dict and sets `Content-Type: application/json`. `data=` sends form encoding
and your Pydantic body model will reject it with a `422`. Using `data=` when you meant `json=` is a
rite of passage; now you can skip it.

Because it's in-process, the tests are **fast** — hundreds per second — and there is no port to
conflict, nothing to wait for, and no flakiness from a slow startup.

> 🎯 **Remember this** — `TestClient(app)` gives you a real HTTP interface with no HTTP. Same code
> path, no socket.

---

## 2. `dependency_overrides`: the cardboard prep station

This is the payoff for everything you did on Day 4, and the answer to prediction question 2.

```python
def get_conn():                       # production: a real pooled connection
    with engine.connect() as conn:
        yield conn

def fake_conn():                      # test: something that just answers
    yield FakeConnection([{"city": "Utrecht", "temp_max_c": 21.4}])

app.dependency_overrides[get_conn] = fake_conn
```

| Token | Meaning |
|---|---|
| `app.dependency_overrides` | A plain dict living on the app |
| key `get_conn` | The **function object** you want to replace |
| value `fake_conn` | What to call instead |

One dictionary entry, and every handler that says `Depends(get_conn)` now receives the fake. You
edited **no handler**. The waiter's script is unchanged; you swapped the prep station for a cardboard
one.

This only works because the handler *asks* rather than *builds*. Had it called `create_engine(URL)`
in its own body, your only options would be starting a real database or monkey-patching module
globals — the fragile approach where tests break whenever someone moves an import.

### Always clean up

`dependency_overrides` mutates the app object, which is shared between tests. Leave an override in
place and it silently leaks into unrelated tests, producing the worst kind of failure: one that
depends on test *order*.

Use a fixture with `yield`, the same setup/teardown shape as Day 4:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from insight_api.main import app
from insight_api.deps import get_conn

@pytest.fixture
def client_with_fake_db():
    app.dependency_overrides[get_conn] = fake_conn
    yield TestClient(app)
    app.dependency_overrides.clear()      # teardown: ALWAYS
```

You met `conftest.py` in Module 2 Day 8: fixtures defined there are available to every test file in
that directory tree without importing them. Same rules apply here.

> 🎯 **Remember this** — `app.dependency_overrides[real] = fake` is the whole trick, and
> `.clear()` in teardown is what keeps it from poisoning other tests.

### 🔁 Recall check

<details>
<summary>A colleague tests by starting the real server with <code>subprocess</code>, sleeping 2 seconds, and sending requests to <code>localhost:8000</code>. List three things that are worse about this.</summary>

1. **Slow** — 2 seconds per test run at best, and the sleep is a guess that is either wasteful or
   too short on a loaded CI runner.
2. **Flaky** — port 8000 may be occupied; the sleep may expire before the app is ready; the process
   may not shut down cleanly and leaks into the next run.
3. **Needs the real world** — a real database must exist, so the tests can't run in CI without one,
   and they mutate shared state.
4. **Bad failures** — when it breaks you get "connection refused", which tells you nothing about
   which line was wrong. `TestClient` gives you the actual Python traceback.

`TestClient` removes all four, because the network was never the thing under test.
</details>

---

## 3. What to assert — the contract, not the implementation

Prediction question 3, and it decides whether your test suite helps or hinders.

```python
# ❌ brittle: breaks when anything is added
assert response.json() == {"city": "Utrecht", "temp_max_c": 21.4}

# ✅ robust: asserts what you actually promised
body = response.json()
assert response.status_code == 200
assert body["city"] == "Utrecht"
assert body["temp_max_c"] == pytest.approx(21.4)
```

A test should fail when **behaviour someone depends on** changes — not when an unrelated field is
added. Exact-equality assertions turn every additive change into a wall of red, and a suite that
cries wolf is a suite people stop reading.

The exception: when the *complete shape* is the promise — a `response_model` that must never leak a
field — assert on the key set deliberately:

```python
assert set(body) == {"id", "email"}          # password_hash must NOT appear. This IS the contract
```

`pytest.approx` you met in Module 2: floats that came through JSON, a `Decimal`, and a database
round-trip are not reliably `==` to a literal.

### The five things worth asserting for an endpoint

| # | Assert | Example |
|---|---|---|
| 1 | The status code | `assert r.status_code == 200` |
| 2 | The shape | `assert "city" in body` |
| 3 | Key values | `assert body["city"] == "Utrecht"` |
| 4 | **The unhappy path** | `assert client.get("/cities/Nowhere").status_code == 404` |
| 5 | **The security boundary** | `assert "password_hash" not in body` |

Rows 4 and 5 are the ones people skip, and they're where the bugs live. Anyone will test that the
happy path returns `200`. Far fewer check that a bad request returns `422` rather than `500`, or that
the response model really is filtering.

> 🎯 **Remember this** — test the **contract**, not the exact payload. Always test one failure case
> per endpoint.

---

## 4. Testing validation

You wrote no validation code on Day 3 — the models did it. So test the models' *effects*, because
those are what callers experience:

```python
def test_rejects_bad_latitude(client):
    r = client.post("/cities", json={"name": "X", "latitude": 500, "longitude": 5})
    assert r.status_code == 422

    fields = [tuple(e["loc"]) for e in r.json()["detail"]]
    assert ("body", "latitude") in fields          # the error points at the RIGHT field
```

That second assertion matters more than it looks. `422` alone doesn't prove the doorman rejected the
right thing — a validator on the wrong field also produces `422`. Checking `loc` proves the error
message will actually help the caller.

### `parametrize` for the grid

Module 2 Day 8 introduced this; here's where it earns its keep:

```python
import pytest

@pytest.mark.parametrize(
    ("payload", "bad_field"),
    [
        ({"name": "", "latitude": 52.0, "longitude": 5.0}, "name"),
        ({"name": "X", "latitude": 500, "longitude": 5.0}, "latitude"),
        ({"name": "X", "latitude": 52.0, "longitude": 999}, "longitude"),
        ({"latitude": 52.0, "longitude": 5.0}, "name"),                 # missing entirely
    ],
)
def test_validation_rejects(client, payload, bad_field):
    r = client.post("/cities", json=payload)
    assert r.status_code == 422
    assert any(e["loc"][-1] == bad_field for e in r.json()["detail"])
```

Four test cases, one function, and each is reported separately by pytest — so a failure names the
exact payload rather than "the validation test failed".

---

## 5. Two layers: unit and integration

Your Module 2 project drew this line and so does this one.

| | Unit tests | Integration tests |
|---|---|---|
| Dependencies | Overridden with fakes | Real database |
| Speed | Milliseconds | Seconds |
| Run in CI on every push | ✅ always | Only with a service container |
| Prove | Your logic and contracts | Your **SQL** and wiring |
| When the DB is down | Pass | **Skip** |

The skip pattern is the one you already shipped in Module 2:

```python
@pytest.fixture(scope="module")
def real_engine():
    eng = create_engine(settings.database_url)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("No database reachable - start docker compose to run integration tests")
    yield eng
```

`scope="module"` means the fixture is built once per test file rather than once per test — worth it
when setup is expensive.

And the warning from Module 2 stands, doubled: **a green `pytest` with everything skipped proves
nothing about your SQL.** Watch the summary line. `12 passed, 4 skipped` and `16 passed` are very
different results, and only one of them tested your queries.

> 🎯 **Remember this** — unit tests prove your **contracts**, integration tests prove your **SQL**.
> Skipped is not passed.

---

## 6. Async endpoints in tests

Day 6 introduces `async def` handlers. `TestClient` handles them transparently — it runs an event
loop internally, so your tests stay ordinary synchronous functions. Nothing changes.

You only need the async client when the *test itself* must await something:

```python
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.anyio
async def test_async_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/weather/daily?city=Utrecht")
    assert r.status_code == 200
```

| Token | Meaning |
|---|---|
| `ASGITransport(app=app)` | Send requests straight into the app, no sockets |
| `base_url="http://test"` | A dummy base; nothing resolves it, but URLs need a host |
| `@pytest.mark.anyio` | Tells pytest to run this coroutine (needs the `anyio` plugin) |

Start with `TestClient`. Reach for this only when you need it.

---

## 7. Structuring the suite

```
tests/
├── conftest.py              # fixtures shared by every file below
├── fixtures/
│   └── weather_rows.json    # canned data, as in Module 2
├── test_health.py           # unit
├── test_weather.py          # unit, with dependency_overrides
└── test_db_integration.py   # integration, skips without a database
```

One file per router keeps failures readable: a red `test_weather.py` tells you where to look before
you've read a single line.

Run them the way Module 2 taught:

```bash
pytest -v                                   # all, verbose
pytest tests/test_weather.py                # one file
pytest tests/test_weather.py::test_daily_ok # one test
pytest -k "validation"                      # by name substring
pytest -x                                   # stop at first failure
pytest --lf                                 # re-run only last failures
```

---

## 🔁 Spaced review

<details>
<summary>1. (Day 4) Why is <code>dependency_overrides</code> impossible for a handler that calls <code>create_engine()</code> in its own body?</summary>

Because there is no seam. `dependency_overrides` works by replacing what FastAPI *resolves* for a
`Depends(...)` marker. A handler that builds its own engine never asks FastAPI for anything, so
there's nothing to override — your only lever is monkey-patching a module-level name, which is
fragile and breaks when imports move.

"Ask, don't build" isn't style advice. It's what creates the seam that tests need.
</details>

<details>
<summary>2. (Day 3) Which test would have caught a new <code>password_hash</code> column leaking into <code>GET /users/42</code>?</summary>

`assert set(body) == {"id", "email"}` — asserting the **exact key set**. This is the one place where
exact equality is right, because the complete shape *is* the promise. A test asserting only
`body["email"] == ...` passes happily while the hash leaks alongside it.
</details>

<details>
<summary>3. (Module 2, Day 8) Your CI shows <code>6 passed</code> and is green, but the endpoint 500s in production on its first real request. What class of test was missing?</summary>

Integration. The unit tests overrode the database dependency, so the **SQL was never executed**.
A typo in a column name, a schema that doesn't exist, or a `Decimal` that no `response_model`
converts all survive a fully-green unit suite.

The fix is what Module 2's `pipeline.yml` did: a workflow job with a Postgres **service container**
that runs the integration tests against a real database.
</details>

---

## 📌 Day 5 on one screen

```python
from fastapi.testclient import TestClient

client = TestClient(app)                      # no server, no port, no network

def test_ok():
    r = client.get("/cities", params={"limit": 5})
    assert r.status_code == 200               # 1. status
    assert "name" in r.json()[0]              # 2. shape

def test_not_found():
    assert client.get("/cities/Nowhere").status_code == 404      # 4. unhappy path

def test_no_leak():
    assert set(client.get("/users/1").json()) == {"id", "email"} # 5. security boundary

# THE SWAP  (fixture, so teardown is guaranteed)
app.dependency_overrides[get_conn] = fake_conn
...
app.dependency_overrides.clear()
```

| | |
|---|---|
| `json=` vs `data=` | JSON body vs form encoding. You want `json=` |
| Assert the contract | not the exact payload... |
| ...except | when the exact key set **is** the contract |
| unit vs integration | contracts vs SQL |
| `12 passed, 4 skipped` | **is not** `16 passed` |

---

## ➡️ Next

Notebook **[10_api_testing_practice.ipynb](10_api_testing_practice.ipynb)** — write the suite, watch
a real failure message, override a dependency, and prove to yourself the handler never noticed.

That closes Week A: you can build and test an API. **Week B ships it** — async, Docker, and Azure.
