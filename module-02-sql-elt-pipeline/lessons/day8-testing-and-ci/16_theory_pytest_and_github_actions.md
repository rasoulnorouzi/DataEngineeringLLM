# Day 8 Theory (Bridge Lesson): pytest, ruff & GitHub Actions — Your Safety Net

**Time:** ~2 h reading, then practice: either the notebook
[17_testing_and_ci_practice.ipynb](17_testing_and_ci_practice.ipynb) (~90 min, recommended —
same drills with the explanations next to the output) or the terminal lab in §18 (~45 min).
**Prerequisites:** Days 6–7. Also skim [docs/GIT_GITHUB_GUIDE.md](../../../docs/GIT_GITHUB_GUIDE.md)
if Git/GitHub still feels shaky.

> **Why "bridge" lesson?** Testing and CI formally belong to Module 1's project layer, but your
> pipeline project needs them *now*. This is the from-zero version; Module 1's `datacli` project
> will deepen it.

**What this lesson has to get you to.** On Days 9–10 you will, on your own:

| You will have to… | Covered in |
|---|---|
| Run the project's test suite and understand every line it prints | §2, §4, §5 |
| Break a test on purpose and read the failure (Milestone 2) | §5 |
| Write a **new** integration test for a mart you invented (Milestone 4) | §6, §7, §9 |
| Get past `ruff check .` — the gate that fails CI most often | §10 |
| Read and edit two YAML workflow files | §11, §12, §13 |
| Publish the repo, get a **green badge**, run the scheduled workflow (Milestone 5) | §14, §15, §16 |
| Debug a build that is green locally and red in CI | §17 |

If you can do those seven things, Days 9–10 are a pleasant afternoon instead of a fight.

**Contents**

*Part A — Testing:* 1 why · 2 making pytest work at all · 3 pytest in ten minutes ·
4 reading output · 5 the command line · 6 fixtures & `conftest.py` · 7 unit vs integration ·
8 what to test (and what not) · 9 writing the project's new test
*Part B — The other gate:* 10 ruff
*Part C — CI:* 11 what CI is · 12 YAML crash course · 13 `ci.yml` and `pipeline.yml` annotated ·
14 secrets & config · 15 schedules & cron · 16 badges & publishing · 17 when CI is red
*Part D — Doing it:* 18 hands-on lab · 19 interview answers · 20 summary

---

# Part A — Testing

## 1. Why Tests Exist (it's not about finding bugs today)

**Analogy — the smoke detector.** You don't install smoke detectors because your house is on fire.
You install them so that *the day something smolders*, you know in seconds instead of when the
roof collapses.

Tests are smoke detectors for code. Their real value is not today — you just wrote the code, you
know it works. Their value is **in three months**, when you change the fetch function for the
KNMI stretch goal and accidentally break date handling. Without tests: your pipeline silently
loads garbage for weeks. With tests: a red ❌ within a minute of the change.

This changes how you *feel* about changing code. Untested code becomes something you're afraid to
touch. Tested code you can refactor fearlessly — the detectors will scream if you break something.
That fearlessness is the actual product.

**The pipeline-specific reason.** Your pipeline runs at 05:00 while you sleep, against an API you
don't control, writing to a database nobody watches. There is no user to complain. The *only*
thing standing between "silently loading garbage since Tuesday" and "you knew within one run" is
an automated check. That's this lesson.

---

## 2. Step Zero: Making `pytest` Work At All

Ninety percent of beginner pain with pytest is not about tests. It's this one error:

```
ModuleNotFoundError: No module named 'pipeline'
```

Understand this now and you will never lose an evening to it.

### The problem

Your test says `from pipeline.fetch import reshape_daily`. Python resolves that by searching
`sys.path` — a list of folders. Your project's code lives in `src/pipeline/`, which is **not** on
that list. Python has no idea your project exists.

### The fix (one command, already in the guide)

```bash
pip install -e ".[dev]"
```

Read it in three pieces:

| Piece | Meaning |
|---|---|
| `pip install .` | "Install the package described by the `pyproject.toml` in this folder" |
| `-e` | **editable**: don't copy the code into site-packages, just point at `src/`. Edits take effect immediately — no reinstall after every change |
| `"[dev]"` | also install the `dev` optional-dependencies group (here: `pytest`, `ruff`) |

The quotes matter on some shells (`zsh` treats `[...]` as a glob). Keep them everywhere.

What makes it work is this block in [`pyproject.toml`](../../project-nl-open-data-pipeline/pyproject.toml):

```toml
[tool.setuptools.packages.find]
where = ["src"]                 # "the packages live under src/"
```

After the install, `import pipeline` works from **any** directory — which is why
`python -m pipeline.run` works, why the tests import cleanly, and why CI can do the same thing on
a fresh machine. This layout (`src/<package>/`) is called the **src layout** and it's the modern
Python standard; the whole point is that you can only import your code *if you installed it*,
exactly like your users will.

### How pytest finds your tests

pytest walks the folders and collects:

- files named `test_*.py` (or `*_test.py`)
- inside them, functions named `test_*`
- (and classes named `Test*`, which we won't use)

Where it starts walking is set in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]           # `pytest` with no arguments = `pytest tests/`
```

pytest also prints a **rootdir** line on startup. That's the folder it considers "the project"
(it finds it by looking for `pyproject.toml`). If rootdir is wrong, you are in the wrong
directory — `cd` into `project-nl-open-data-pipeline/` and try again.

### The 60-second checklist when imports break

```bash
python -c "import pipeline; print(pipeline.__file__)"   # does Python see it at all?
pip list | grep nl-open-data-pipeline                    # Windows: pip list | findstr nl-open
where python                                             # Windows  ) is the venv
which python                                             # Linux/Mac) actually active?
```

| Symptom | Cause | Fix |
|---|---|---|
| `No module named 'pipeline'` | not installed in the **active** venv | activate the venv, `pip install -e ".[dev]"` from the project folder |
| `pytest: command not found` | pytest installed in a different venv (or not at all) | same as above; then `python -m pytest` also works |
| `collected 0 items` | you're in the wrong folder, or the file isn't named `test_*.py` | check the rootdir line pytest printed |
| Import works in your editor, not in the terminal | the editor uses a different interpreter | VS Code: *Python: Select Interpreter* → the module `.venv` |

---

## 3. pytest in Ten Minutes

The rules are almost embarrassingly simple:

1. Test files are named `test_*.py` (in the `tests/` folder)
2. Tests are plain functions named `test_*`
3. Inside, you `assert` things
4. Run `pytest` — it finds and runs everything, `.` per pass, `F` per fail

```python
# src/pipeline/fetch.py  (the code under test — this is the real project file)
def reshape_daily(daily: dict) -> list[dict]:
    """Turn Open-Meteo's parallel arrays into one record per day."""
    return [
        {"obs_date": d, "temp_max": tmax, "temp_min": tmin, "precip_mm": prec}
        for d, tmax, tmin, prec in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_sum"],
            strict=True,          # arrays of different lengths = corrupt source data -> fail loudly
        )
    ]
```

```python
# tests/test_fetch.py
from pipeline.fetch import reshape_daily


def test_reshape_pairs_values_by_position():
    # Arrange
    daily = {
        "time": ["2026-07-01", "2026-07-02"],
        "temperature_2m_max": [22.4, 19.8],
        "temperature_2m_min": [12.1, 11.3],
        "precipitation_sum": [0.0, 4.2],
    }

    # Act
    records = reshape_daily(daily)

    # Assert
    assert len(records) == 2
    assert records[0] == {
        "obs_date": "2026-07-01", "temp_max": 22.4, "temp_min": 12.1, "precip_mm": 0.0,
    }


def test_reshape_empty_input_gives_empty_list():
    daily = {"time": [], "temperature_2m_max": [],
             "temperature_2m_min": [], "precipitation_sum": []}
    assert reshape_daily(daily) == []
```

### The pattern behind every good test: Arrange–Act–Assert

1. **Arrange** — build the input (a small fake `daily` dict)
2. **Act** — call the function **once**
3. **Assert** — check the result

One behaviour per test, named after the behaviour
(`test_reshape_pairs_values_by_position`), so the failure message reads like a sentence telling
you what broke. A test named `test_1` tells you nothing at 06:00 when the night shift is red.

### Three properties of a test you can trust

- **Independent** — it passes whether it runs first, last, or alone. Never rely on another test
  having run before (that's why the DB tests below clean up after themselves).
- **Deterministic** — same input, same verdict, every time. No live network, no `date.today()`
  in the *expected* value. Note how the project's test passes `today=date(2026, 7, 17)`
  explicitly instead of letting the clock decide — a test that passes today and fails on
  1 January is worse than no test.
- **Fast** — you should be willing to run the whole suite after every save. The four unit tests
  here take milliseconds.

---

## 4. Reading pytest Output (you will spend more time here than writing tests)

### A green run

```
$ pytest -v
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.2.0, pluggy-1.5.0
rootdir: /.../project-nl-open-data-pipeline           ← the folder pytest considers "the project"
configfile: pyproject.toml
collected 6 items                                      ← how many tests it FOUND

tests/test_db_integration.py::test_upsert_is_idempotent PASSED           [ 16%]
tests/test_db_integration.py::test_transform_builds_staging_and_marts PASSED [ 33%]
tests/test_fetch.py::test_date_window_ends_yesterday PASSED              [ 50%]
tests/test_fetch.py::test_reshape_pairs_values_by_position PASSED        [ 66%]
tests/test_fetch.py::test_reshape_keeps_null_values_for_raw_layer PASSED [ 83%]
tests/test_fetch.py::test_reshape_empty_input_gives_empty_list PASSED    [100%]

============================== 6 passed in 0.42s ===============================
```

`collected 6 items` is the number to sanity-check first. If it says `collected 0 items`, nothing
ran and green means nothing (see §2).

### A failing run — and the best feature in pytest

Say someone swaps two lines so `temp_min` gets the max value. Run again:

```
=================================== FAILURES ===================================
__________________ test_reshape_pairs_values_by_position _______________________

    def test_reshape_pairs_values_by_position(open_meteo_payload):
        records = reshape_daily(open_meteo_payload["daily"])

        assert len(records) == 3
>       assert records[0] == {
            "obs_date": "2026-07-01",
            "temp_max": 22.4,
            "temp_min": 12.1,
            "precip_mm": 0.0,
        }
E       AssertionError: assert {'obs_date': '2026-07-01', 'precip_mm': 0.0, 'temp_max': 22.4, 'temp_min': 22.4} == {'obs_date': '2026-07-01', 'precip_mm': 0.0, 'temp_max': 22.4, 'temp_min': 12.1}
E         Common items:
E         {'obs_date': '2026-07-01', 'precip_mm': 0.0, 'temp_max': 22.4}
E         Differing items:
E         {'temp_min': 22.4} != {'temp_min': 12.1}                       ← THE ANSWER
E
E         Full diff: ...

tests/test_fetch.py:21: AssertionError
=========================== short test summary info ============================
FAILED tests/test_fetch.py::test_reshape_pairs_values_by_position - AssertionError: ...
========================= 1 failed, 5 passed in 0.38s ==========================
```

How to read it, in order:

1. **The bottom line first** — `1 failed, 5 passed`. How bad is it?
2. **`short test summary info`** — *which* tests failed, by name. With 40 tests this is the only
   part you read at first.
3. **The `>` marker** — the exact line that blew up.
4. **The `E` lines** — pytest's **assertion introspection**: it rewrites your `assert` so it can
   show you *both sides* and the diff. This is why you write plain `assert a == b` and never
   `assert check(a, b)` — plain asserts give you the diff, wrapped ones give you `assert False`.
5. **The last line of the traceback** — `tests/test_fetch.py:21` — file and line, clickable in
   VS Code.

**Errors vs failures.** `FAILED` = an assert was false (your code is wrong, or your expectation
is). `ERROR` = the test crashed before/around asserting — usually a broken fixture, a missing
import, or a database that isn't there. Different causes, different fixes: an ERROR usually means
your *setup* is broken, not your code.

---

## 5. The pytest Command Line You Actually Need

You'll use maybe seven flags for the rest of your career:

```bash
pytest                       # everything, quiet-ish
pytest -v                    # verbose: one line per test (use this by default)
pytest -q                    # quiet: just dots and the summary
pytest -x                    # stop at the FIRST failure (fast feedback while fixing)
pytest --lf                  # "last failed": rerun only what failed last time
pytest -k "idempotent"       # only tests whose name matches this expression
pytest tests/test_fetch.py   # only this file
pytest tests/test_fetch.py::test_reshape_empty_input_gives_empty_list   # only this ONE test
pytest --tb=short            # shorter tracebacks (or --tb=line for one line each)
pytest -s                    # don't swallow print() output — poor man's debugger
pytest -ra                   # summary of skipped/xfailed reasons (why did it skip?)
```

The workflow when something is red:

```bash
pytest -x -q            # 1. find the first failure fast
pytest -k "the_name" -v # 2. iterate on just that test while you fix
pytest -v               # 3. full suite again before committing
```

> **Milestone 2 preview.** The project asks you to comment out the `ON CONFLICT` clause in
> `load.py`, run `pytest -v`, and watch `test_upsert_is_idempotent` go red with
> `assert 4 == 2`. That "4" is the duplicate rows. Breaking a test on purpose and reading its
> scream is the single fastest way to learn what a test protects. Do it.

---

## 6. Fixtures: Shared Setup, and `conftest.py`

**Analogy — *mise en place*.** A chef doesn't chop onions in the middle of cooking; everything is
prepped in little bowls before the pan gets hot. A **fixture** is a prepped bowl: setup code that
runs before your test and hands it something ready to use.

A test asks for a fixture simply by naming it as a parameter. No import, no wiring:

```python
# tests/conftest.py — pytest loads this file automatically for every test in this folder
import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def open_meteo_payload() -> dict:
    """A saved real-shaped API response (never call the live API in unit tests)."""
    return json.loads((FIXTURES / "open_meteo_sample.json").read_text(encoding="utf-8"))
```

```python
# tests/test_fetch.py
def test_reshape_keeps_null_values_for_raw_layer(open_meteo_payload):   # ← name matches ↑
    records = reshape_daily(open_meteo_payload["daily"])
    assert records[2]["temp_max"] is None
```

Four facts that explain everything:

1. **`conftest.py` is magic by convention.** Any fixture defined there is available to every test
   file in that folder and below — no import statement. It's pytest's "shared kitchen".
2. **Parameter name = fixture name.** That's the entire wiring mechanism.
3. **Two meanings of "fixture".** The `@pytest.fixture` *function*, and the saved sample data
   file (`tests/fixtures/open_meteo_sample.json`) it reads. In data work you'll hear both;
   context tells you which.
4. **Note the deliberate `null`** in that JSON file. The sample isn't just "some data" — it was
   built to pin down an edge case you saw live in Day 7: the archive lags a day, so the newest
   day can be `null`. The raw layer must keep the null; staging SQL filters it. That test is a
   written-down design decision.

### Setup *and* teardown: `yield`

A fixture that needs to clean up uses `yield` instead of `return`. Everything before the `yield`
is setup; everything after runs when the tests are done — pass or fail.

```python
@pytest.fixture(scope="module")
def engine():
    eng = create_engine(config.DATABASE_URL)
    try:                                              # ── setup
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))            # can we actually reach Postgres?
    except Exception:
        pytest.skip("No database reachable - start docker compose to run integration tests")

    yield eng                                         # ── the tests run here

    with eng.begin() as conn:                         # ── teardown, always runs
        conn.execute(text("DELETE FROM raw.weather_daily WHERE city = 'Testville'"))
```

That's the real `engine` fixture from
[`tests/test_db_integration.py`](../../project-nl-open-data-pipeline/tests/test_db_integration.py).
Three things worth stealing forever:

- **`pytest.skip()` inside a fixture skips every test that asked for it**, with a reason. That's
  how `pytest` stays green on a laptop with Docker off — a skip is not a failure.
- **The teardown deletes the test's own rows**, so the suite is rerunnable and doesn't pollute
  your real data. Test data is clearly branded (`'Testville'`) so it can never be confused with
  a real city.
- **`scope=`** controls how often the fixture runs:

| scope | Runs once per… | Use for |
|---|---|---|
| `function` (default) | each test | cheap things: dicts, temp files |
| `module` | each test *file* | expensive things: a DB engine ← our case |
| `session` | whole `pytest` run | very expensive: starting a container |

A default-scope fixture gives every test a **fresh** object — that's what keeps tests
independent. Widen the scope only when setup is genuinely expensive, and then be careful that
tests don't leak state into each other.

### Built-in fixtures worth knowing

- `tmp_path` — a fresh temporary directory (a `pathlib.Path`) per test. Use it whenever a test
  writes a file; never write into the repo.
- `capsys` — capture `print()` output to assert on it.
- `monkeypatch` — temporarily set an environment variable or replace an attribute, undone
  automatically afterwards. E.g. `monkeypatch.setenv("DATABASE_URL", "…")`.

---

## 7. Two Kinds of Test: Unit and Integration

This distinction is on every data-engineering job description. Learn the words with the example
in front of you.

| | **Unit test** | **Integration test** |
|---|---|---|
| Tests | one function's logic, alone | several parts working *together* |
| Needs | nothing (no network, no DB) | real infrastructure — your Docker Postgres |
| Speed | milliseconds | seconds |
| In this project | `tests/test_fetch.py` (4 tests) | `tests/test_db_integration.py` (2 tests) |
| When it fails | your logic is wrong | the wiring, SQL, or environment is wrong |
| Runs in `ci.yml`? | yes | no — skips politely, no DB there |
| Runs in `pipeline.yml`? | — | **yes**, against a real throwaway Postgres |

**Why both?** A unit test proves `reshape_daily` pairs values correctly. It cannot prove that the
`ON CONFLICT` clause actually prevents duplicates in PostgreSQL — only a real database can answer
that. And an integration suite alone would be slow and would point at "something in these 200
lines is wrong" instead of at one function. You want a lot of the first and a few well-chosen
ones of the second.

**The classic pyramid:** many fast unit tests at the bottom, fewer integration tests in the
middle, a handful of end-to-end runs at the top. Your project is exactly that shape — and
`pipeline.yml` (fetch the live API → load → transform, nightly) *is* the end-to-end tip.

### The two integration tests, and why they're the right two

```python
def test_upsert_is_idempotent(engine):
    load.ensure_raw_schema(engine)

    load.upsert_raw(engine, SAMPLE_RECORDS)
    load.upsert_raw(engine, SAMPLE_RECORDS)      # the light-switch test: run it twice

    with engine.connect() as conn:
        n = conn.execute(
            text("SELECT count(*) FROM raw.weather_daily WHERE city = 'Testville'")
        ).scalar()
    assert n == 2                                 # not 4!
```

Day 6 promised idempotency in prose. **This turns the promise into an executable fact** — a
sentence in a README rots, a test can't. If anyone ever "optimises" the upsert into a plain
INSERT, this goes red before the duplicate rows reach production.

The second one, `test_transform_builds_staging_and_marts`, asserts that the SQL files ran **in
order** (`executed == ["10_staging_weather.sql", "20_marts_weather.sql"]`) and that a known
input produces a known output two layers down (2 staging rows, a weekly row with
`days_observed = 2`). That's a *contract test* on your ELT: input shape → output shape.

### Gotcha: Postgres `numeric` comes back as `Decimal`

Your marts use `round(avg(...), 1)` → PostgreSQL `numeric` → psycopg2 hands Python a
`decimal.Decimal`, not a `float`. Mostly harmless, occasionally baffling:

```python
from decimal import Decimal
Decimal("20.5") == 20.5      # True  — exactly representable
Decimal("0.1")  == 0.1       # False — the float 0.1 isn't exactly 0.1
```

So when you assert on an averaged number, convert first and compare with a tolerance:

```python
assert float(avg_temp) == pytest.approx(20.5)      # tolerant of float noise
```

`pytest.approx` is the right tool for *any* float comparison (`0.1 + 0.2 == 0.3` is `False` in
every language with floats). Counts (`count(*)`) come back as plain `int` — compare those
normally.

### Optional pro touch: marking integration tests

The project skips DB tests by *probing* the database. The other common approach is a **marker**:

```python
@pytest.mark.integration
def test_upsert_is_idempotent(engine): ...
```

```toml
# pyproject.toml — register the marker so pytest doesn't warn about a typo'd name
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["integration: needs a running PostgreSQL"]
```

```bash
pytest -m "not integration"    # unit tests only (what you'd run in ci.yml)
pytest -m integration          # only the DB ones
```

Both approaches are professional. Probing is friendlier for a course (nobody has to remember a
flag); markers are more explicit at scale. Knowing both is an easy interview point.

---

## 8. What to Test — and What Not To

- ✅ **Your logic**: reshaping, the date window, SQL-building, filtering, anything with an `if`
- ✅ **Your edge cases**: empty input, `None` values, a day missing, an empty API response
- ✅ **Your contracts**: "reruns don't duplicate", "SQL files run in this order", "the mart has
  one row per city-week"
- ❌ **Other people's code**: don't test that `requests` performs HTTP or that Postgres can INSERT.
  That's their test suite's job
- ❌ **The live API in unit tests**: slow, flaky, rate-limited, impolite, and red at 3 a.m. for
  reasons that aren't your fault. Test *your handling* of a **saved** response instead
- ❌ **Trivia**: getters, constants, `__init__` assigning three attributes

### The order to write them in when you extend the pipeline

1. What's the **riskiest** thing that could silently go wrong? (Usually: duplicates, silent
   dropped rows, wrong dates.) Test that first.
2. What did you have to think about while writing the code? Every "hmm, what if…" is a test.
3. Every bug you actually hit → write the test that would have caught it, *then* fix the bug.
   That's a **regression test**, and it's how suites grow where they matter instead of where
   it's easy.

### Two more tools you'll want

**Parametrize** — same test body, many inputs, reported as separate tests:

```python
import pytest
from datetime import date
from pipeline.fetch import date_window


@pytest.mark.parametrize(
    "days, expected_start",
    [
        (1, date(2026, 7, 16)),
        (7, date(2026, 7, 10)),
        (30, date(2026, 6, 17)),
    ],
)
def test_date_window_length(days, expected_start):
    start, end = date_window(today=date(2026, 7, 17), days=days)
    assert end == date(2026, 7, 16)      # always yesterday
    assert start == expected_start
```

Three tests, one body — and a failure names the exact case: `test_date_window_length[30-...]`.

**`pytest.raises`** — assert that something *fails* the way it should:

```python
def test_reshape_rejects_missing_key():
    with pytest.raises(KeyError):
        reshape_daily({"time": ["2026-07-01"]})     # no temperature arrays at all
```

Error paths are behaviour too. "It raises a clear error on bad input" is a feature worth pinning.

### How much testing is enough?

For this project: the four unit tests + two integration tests are the honest minimum, and your
milestone adds a third integration test. The professional answer to "what's your coverage
target?" is not a number — it's **"every behaviour I'd be scared to break"**. Optional: install
`pytest-cov` and run `pytest --cov=pipeline` to see which lines never execute. Useful as a
spotlight on forgotten branches; useless as a score to chase.

---

## 9. Worked Example: The Test You Have to Write on Day 10

Milestone 3 asks you to add `sql/30_marts_rankings.sql` (a `RANK()` over weekly rainfall).
Milestone 4 asks you to test it. Here is the *thinking*, so that milestone is a 20-minute job.

**Step 1 — what could silently go wrong?** The new SQL file might not run at all (wrong folder,
wrong extension), might run in the wrong order (it depends on `marts.weather_weekly` existing),
or the ranking could be inverted (driest first). All three are invisible without a test.

**Step 2 — pick the layer.** It's SQL against real tables → integration test, in
`tests/test_db_integration.py`, reusing the `engine` fixture.

**Step 3 — Arrange–Act–Assert with the fixtures already there.**

```python
def test_rankings_mart(engine):
    # Arrange: known input, branded so teardown can remove it
    load.ensure_raw_schema(engine)
    load.upsert_raw(engine, SAMPLE_RECORDS)

    # Act: run the whole transform chain
    executed = transform.run_sql_files(engine)

    # Assert 1: the new file ran, and ran last
    assert executed == [
        "10_staging_weather.sql",
        "20_marts_weather.sql",
        "30_marts_rankings.sql",
    ]

    # Assert 2: the mart says what it should for our known input
    with engine.connect() as conn:
        rank = conn.execute(
            text("SELECT precip_rank FROM marts.city_rankings WHERE city = 'Testville'")
        ).scalar()
    assert rank == 1        # only city in the test data -> rank 1
```

**Step 4 — remember the ripple.** `test_transform_builds_staging_and_marts` asserts the *same*
`executed` list. Adding a SQL file makes that older test red — correctly! Update it too. A test
going red because you changed intended behaviour is the system working; update the expectation
deliberately, never by deleting the assert.

**Step 5 — watch it fail first.** Run `pytest -k rankings -v` *before* writing the SQL file. It
should fail with `relation "marts.city_rankings" does not exist`. A test you've never seen fail
is a test you don't know works.

---

# Part B — The Other Gate

## 10. ruff: The Linter That Will Fail Your CI First

Honest prediction: your first red CI run will not be `pytest`. It will be `ruff check .`.

**A linter is a spell-checker for code.** A spell-checker doesn't judge whether your essay is
*good* — it catches "teh", the double "the the", and the sentence you started and never finished.
Ruff does the same for Python: unused imports, undefined names, unused variables, lines that are
too long, imports in a weird order. It's fast (written in Rust) and it has replaced a whole
generation of tools (`flake8`, `isort`, `pyupgrade`, partly `black`).

### The three commands

```bash
ruff check .            # report problems (this is what CI runs)
ruff check --fix .      # fix the ones it can fix safely (imports, ordering, simple rewrites)
ruff format .           # reformat code style (spacing, quotes, line breaks) - optional here
```

`ruff check .` exits non-zero when it finds anything → the CI step goes red → the whole run is
red. That's the entire mechanism.

### Reading its output

```
src/pipeline/fetch.py:5:1: F401 [*] `os` imported but unused
  |
3 | import json
4 | import logging
5 | import os
  | ^^^^^^^^^ F401
  |
  = help: Remove unused import: `os`

Found 1 error.
[*] 1 fixable with the `--fix` option.
```

`file:line:column`, a **rule code**, the problem, and often the fix. The codes you'll meet:

| Code | Means | Why it matters (it's not pedantry) |
|---|---|---|
| `F401` | imported but unused | leftovers from deleted code; misleads the next reader |
| `F821` | undefined name | a real bug — a typo'd variable that would crash at runtime |
| `F841` | local variable assigned but never used | you probably meant to use it |
| `E501` | line too long | this project sets `line-length = 100` in `pyproject.toml` |
| `E712` | `== True` | write `if flag:` |
| `I001` | import block unsorted | consistent import order makes diffs smaller |

The config lives in the same `pyproject.toml` you already know:

```toml
[tool.ruff]
line-length = 100
src = ["src", "tests"]           # so ruff knows YOUR packages from third-party ones

[tool.ruff.lint]
# Pin the rule set explicitly: ruff's defaults grow with new releases, and a rule
# added upstream should never turn your CI red without you changing a line of code.
#   E/W = pycodestyle - F = pyflakes (real bugs) - I = import sorting
#   B = bugbear (likely mistakes) - UP = modern-Python rewrites
select = ["E", "W", "F", "I", "B", "UP"]
```

**Why that `select` block matters — a real CI lesson.** `pyproject.toml` says `ruff>=0.4`, so CI
installs whatever ruff released *this morning*. Ruff adds rules over time; with no `select`, a new
release can fail your build on code you never touched, and the failure has nothing to do with your
change. Pinning the rule set makes the gate **deterministic**: it only changes when *you* change
it. (The same reasoning applies to the tool version — some teams also pin `ruff==0.x.y` and bump it
deliberately.) This project's `B` selection is what caught a genuine bug in `fetch.py`: a `zip()`
without `strict=True` silently drops days if the API ever returns arrays of different lengths.

### The rule that saves you

**Run the same command CI runs, before you push.** Every time:

```bash
ruff check . && pytest -v
```

Two commands, five seconds, and CI stops being a surprise. If ruff flags something you genuinely
disagree with, the professional escape hatch is a targeted `# noqa: E501` comment on that line —
not deleting the CI step.

> Later, optionally: `pre-commit` runs ruff automatically on every `git commit`. Nice, but learn
> the manual habit first — you need to know what the robot is doing for you.

---

# Part C — Continuous Integration

## 11. CI: Why a Robot Should Run Your Checks

Tests only protect you if they *run*. Humans forget, especially at 23:40 on a Friday. So we make a
robot run them on **every push**: that's **Continuous Integration (CI)**.

**Analogy — the bouncer.** `main` is the club: only code that passes the dress code (tests +
linter) gets in. The bouncer never gets tired, never makes exceptions because "it's a tiny
change", and checks *every* guest.

Concretely, with **GitHub Actions** (GitHub's built-in CI service):

1. You push code (or open a pull request)
2. GitHub boots a **fresh** Linux machine in the cloud
3. It checks out your code, installs dependencies, runs `ruff` and `pytest`
4. Green ✅ or red ❌ appears on your commit/PR — and on the **badge** in your README

That fresh machine is the feature, not a detail. It has none of your laptop's history: no
half-installed packages, no file you forgot to commit, no environment variable you set in
March. If it only works on *your* machine, CI says so within a minute.

### The five words of Actions vocabulary

```
Workflow  (a .yml file in .github/workflows/)   "CI"
 └─ triggered by an Event                       push, pull_request, schedule, workflow_dispatch
    └─ contains Jobs                            "test"        ← each gets its own fresh machine
       └─ each Job runs on a Runner             ubuntu-latest ← the VM
          └─ and has Steps, in order            checkout → setup-python → install → ruff → pytest
             └─ a Step either `uses:` an Action  a reusable building block someone published
                        or `run:`s a shell command   exactly what you'd type in your terminal
```

Jobs run **in parallel** by default and are isolated from each other; steps run **in sequence**
in the same workspace. If any step exits non-zero, the job stops and turns red.

**What it costs:** on public repositories, standard runners are free — which is one more reason
your portfolio repos are public. Private repos draw from a monthly minutes allowance on the free
plan (check GitHub's billing page for the current number). Your two workflows use maybe two
minutes a day.

---

## 12. Sixty-Second YAML Crash Course

Workflows are YAML. You met YAML already in `docker/docker-compose.yml`; here are the rules that
actually bite:

```yaml
name: CI                  # key: value  → a string

on:                       # a nested map (note the 2-space indent below)
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:                # a LIST: every item starts with "- "
      - uses: actions/checkout@v4
      - name: Install deps
        run: pip install -e ".[dev]"      # this line belongs to the SAME item as `name:`
      - name: Multi-line command
        run: |                            # "|" = keep the following lines as-is
          echo "line one"
          echo "line two"
```

- **Indentation is structure.** Two spaces per level. **Never tabs** — YAML rejects them outright.
- **`- ` starts a list item.** Keys under it, aligned, belong to that item.
- **Quote strings that contain `:` or start with `*`, `{`, `!`** — e.g. `cron: "0 5 * * *"`.
- `python-version: "3.12"` is quoted **on purpose**: unquoted `3.10` is the number 3.1 and you'd
  silently get Python 3.1… which doesn't exist. Always quote versions.
- Comments start with `#`.

If a workflow doesn't appear in the Actions tab at all, it's almost always invalid YAML or a
wrong filename — the file must be in `.github/workflows/` and end in `.yml`/`.yaml`. GitHub shows
the parse error at the top of the Actions tab; VS Code's YAML extension catches most of them as
you type.

---

## 13. Your Two Workflows, Line by Line

### 13.1 `ci.yml` — the bouncer (every push)

```yaml
name: CI                     # shown in the Actions tab and used by the badge URL

on:                          # WHEN does this run?
  push:                      #   every push to any branch
  pull_request:              #   and every PR (so you see the verdict before merging)

jobs:
  test:                      # a job = one fresh cloud machine
    runs-on: ubuntu-latest   # which machine (Linux — like most servers, and like your future Azure container)

    steps:                   # steps run in order, top to bottom
      - uses: actions/checkout@v4          # step 1: get your code onto the machine.
                                           #   Without this the machine is EMPTY. @v4 pins the
                                           #   major version of a published, reusable Action.
      - uses: actions/setup-python@v5      # step 2: install a specific Python
        with:                              #   `with:` = the Action's parameters
          python-version: "3.12"

      - run: pip install -e ".[dev]"       # step 3: install project + dev tools (§2)
                                           #   `run:` = a shell command, exactly as you'd type it
      - run: ruff check .                  # step 4: the linter gate (§10)
      - run: pytest -v                     # step 5: the smoke detectors
```

That's the whole magic: **a YAML file listing the commands you'd run yourself, executed by a robot
on a clean machine on every push.** Notice that steps 3–5 are literally your local workflow — CI
should never do anything you can't reproduce by hand.

Note what *isn't* here: a database. That's deliberate — the integration tests skip themselves
(§6), so `ci.yml` stays fast and simple. Their real run happens in the second workflow.

*(Optional speedup you may see in other repos: `with: { python-version: "3.12", cache: "pip" }`
caches downloaded packages between runs. Fine to add; not needed at this size.)*

### 13.2 `pipeline.yml` — the night shift (on a schedule, with a real database)

This is the more advanced file, and the one that impresses in interviews. Read it slowly.

```yaml
name: Scheduled pipeline run

on:
  schedule:
    - cron: "0 5 * * *"   # daily at 05:00 UTC (§15)
  workflow_dispatch:       # + a manual "Run workflow" button in the GitHub UI

jobs:
  run-pipeline:
    runs-on: ubuntu-latest

    services:                      # ── SERVICE CONTAINERS ──
      postgres:                    # GitHub starts this Docker container next to your job,
        image: postgres:16         # on the same network, before any step runs.
        env:                       # Same image and credentials as your docker-compose.yml!
          POSTGRES_DB: week2_db
          POSTGRES_USER: student
          POSTGRES_PASSWORD: student123
        ports:
          - 5432:5432              # reachable from the job as localhost:5432
        options: >-                # wait until Postgres actually accepts connections
          --health-cmd "pg_isready -U student -d week2_db"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:                           # environment variables for every step in this job
      DATABASE_URL: postgresql+psycopg2://student:student123@localhost:5432/week2_db

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"

      - name: Run the full pipeline (fetch -> load -> transform)
        run: python -m pipeline.run                    # the REAL thing, against the LIVE API

      - name: Verify results with integration tests
        run: pytest -v tests/test_db_integration.py    # ...and now they do NOT skip
```

Four ideas to take away:

1. **Service containers** are "Docker Compose for CI". Your `docker compose up` on the laptop and
   this `services:` block do the same job for the same reason. (They only work on Linux runners.)
2. **The health check is not optional.** Without it, your first step could connect before Postgres
   has finished booting and fail with `connection refused` — a classic flaky CI failure.
3. **`env: DATABASE_URL`** is the payoff of Day 6's config rule: `config.py` reads the environment
   and falls back to the local default, so the *same code* runs on your laptop, in this job, and
   (Module 3) on Azure. Nothing in `src/` knows it's in CI.
4. **The integration tests stop skipping** because the database is now reachable. Same tests, two
   environments, two behaviours — by design.

This workflow is an **end-to-end smoke test on a timer**: it proves that the API still answers,
your fetch still parses it, the upsert still works, and both SQL layers still build. The database
it fills is thrown away when the job ends — in Module 3 you'll point the same workflow at a
persistent Azure database and it becomes a real production pipeline.

---

## 14. Configuration and Secrets in CI

This project needs no secrets — Open-Meteo is open, and the throwaway Postgres password is
worthless. But the KNMI stretch goal needs an API key, and Module 3 needs Azure credentials, so
learn the rules now.

**Analogy — the house key.** You give the housekeeper a key; you don't tape it to the front door.
Config that isn't secret (a URL, a city list) can live in the repo. Secrets get handed over
separately, and the door can be re-keyed without rebuilding the house.

**The iron rule: never commit a secret.** Not in `config.py`, not in a notebook output, not "just
for a minute" — Git remembers forever, and GitHub's secret scanning will email you (or worse,
someone else finds it first). If it happens: revoke/rotate the key **first**, clean history
second.

How it's done, in the three places you'll meet:

| Where | Mechanism | In this project |
|---|---|---|
| Your laptop | a `.env` file, git-ignored; `.env.example` committed as the template | [`.env.example`](../../project-nl-open-data-pipeline/.env.example) holds the harmless default URL |
| GitHub Actions | repo **Settings → Secrets and variables → Actions** | not needed yet |
| Azure (Module 3) | app settings / Key Vault | later |

In a workflow you reference a secret like this — GitHub injects it at run time and masks it in the
logs (it prints as `***`):

```yaml
    env:
      KNMI_API_KEY: ${{ secrets.KNMI_API_KEY }}      # set in repo Settings, never in the file
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

Two facts worth remembering: secrets are **write-only** (you can never read one back in the UI,
only replace it), and they are **not** exposed to workflows triggered by pull requests from
forks — which is a security feature, and a common "why is my fork's CI failing?" answer.

Note that `.env` files are read by *tools* you add (like `python-dotenv`), not by Python itself;
this project keeps it even simpler — plain environment variables with a default in `config.py`.

---

## 15. The Same Robot, on a Timer: `schedule` and cron

Remember Day 6's question — *who presses "run" every night?* The `on:` block has one more trigger:

```yaml
on:
  schedule:
    - cron: "0 5 * * *"      # every day at 05:00 UTC (= 06:00 or 07:00 in NL)
  workflow_dispatch:          # + a manual "Run workflow" button in the GitHub UI
```

That five-field string is **cron syntax**, the 50-year-old standard for schedules:

```
┌───────── minute        (0)
│ ┌─────── hour          (5)
│ │ ┌───── day of month  (* = every)
│ │ │ ┌─── month         (* = every)
│ │ │ │ ┌─ day of week   (* = every, 0 = Sunday)
0 5 * * *
```

| Expression | Means |
|---|---|
| `0 * * * *` | every hour, on the hour |
| `*/15 * * * *` | every 15 minutes |
| `0 8 * * 1` | Mondays at 08:00 |
| `0 5 1 * *` | the 1st of each month at 05:00 |

Five honest gotchas — every one of them has cost someone a morning:

1. **Times are UTC**, and cron does **not** know about daylight saving. Your 05:00 UTC job runs at
   06:00 Dutch winter time and 07:00 in summer. Pick an hour where that doesn't matter.
2. **GitHub may delay scheduled runs** by minutes (more during peak load). Fine for a daily
   pipeline; never build something that needs to-the-second timing on cron.
3. **Scheduled workflows only run on the default branch** (`main`). Testing a cron change on a
   feature branch does nothing — that's what `workflow_dispatch` is for.
4. **GitHub disables scheduled workflows in repos with no activity for ~60 days** and emails you.
   A quiet portfolio repo goes silent; one click re-enables it.
5. **A new repo's Actions tab may need one manual "I understand" click** before scheduled or
   forked workflows run at all.

Because of #3, `workflow_dispatch` is not a nice-to-have — it's how you test the night shift at
14:00 instead of waiting until tomorrow. Always add it.

So your project gets **two** workflows, with different jobs:

| | `ci.yml` | `pipeline.yml` |
|---|---|---|
| Role | bouncer | night shift |
| Trigger | every push / PR | cron + manual button |
| Database | none (integration tests skip) | throwaway Postgres service container |
| Network | none | the live Open-Meteo API |
| Answers | "is the code still correct?" | "does the whole thing still work end-to-end?" |

Seeing a green scheduled run in your repo's Actions tab every morning is exactly the "automated
nightly runs" claim on your CV — and the public run history is the proof.

---

## 16. Badges, and What "Published" Means

A **badge** is a live status image. GitHub serves one per workflow at a predictable URL, so you
paste two lines into your README and every visitor sees whether the project is currently healthy:

```markdown
[![CI](https://github.com/<your-username>/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/<repo>/actions/workflows/ci.yml)
[![Scheduled pipeline run](https://github.com/<your-username>/<repo>/actions/workflows/pipeline.yml/badge.svg)](https://github.com/<your-username>/<repo>/actions/workflows/pipeline.yml)
```

The pattern: `…/actions/workflows/<filename>.yml/badge.svg` for the image, the same URL without
`/badge.svg` as the link (so clicking it opens the run history). Add `?branch=main` to the image
URL if you want it pinned to your default branch.

Why this matters more than it looks: a recruiter or lead scanning your repo sees, in one glance,
that the project has automated tests, that they pass, and that a scheduled job ran this morning.
That is the difference between "wrote some scripts" and "ships maintained software" — and it's
Milestone 5 of the project.

The publishing steps themselves (copy the folder out, `git init`, push, enable Actions) are in
[docs/GIT_GITHUB_GUIDE.md](../../../docs/GIT_GITHUB_GUIDE.md) → *"Publishing a course project as a
portfolio repo"*.

### The professional loop, now that a bouncer exists

```bash
git checkout -b add-rankings-mart     # 1. branch
# ...write sql/30_marts_rankings.sql + its test...
ruff check . && pytest -v             # 2. run the bouncer's checks LOCALLY
git commit -am "Add city rankings mart with test"
git push -u origin add-rankings-mart  # 3. push -> CI starts automatically
# 4. open a PR on GitHub, watch the check turn green, then merge
```

Step 2 is the habit that makes steps 3–4 boring. Boring is the goal.

---

## 17. When CI Is Red But Your Laptop Is Green

This *will* happen, and it's the most valuable half hour in this lesson. The mindset: the runner
is not being difficult — it's telling you something true about your project that your laptop was
hiding.

**How to investigate:** Actions tab → click the red run → click the failed job → expand the red
step. The log is the whole story; scroll to the **first** error, not the last. "Re-run jobs" is in
the top right (use "Re-run failed jobs" to save time), and every run keeps its full log.

| The red step | Likely cause | Fix |
|---|---|---|
| `actions/checkout` or the file isn't in the run at all | you never committed the file | `git status`, commit, push. The #1 cause, by a mile |
| `pip install -e ".[dev]"` — `ModuleNotFoundError` later | you `pip install`ed something locally but never added it to `pyproject.toml` | add the dependency to `[project] dependencies` |
| `ruff check .` | style/lint issues you never ran locally | `ruff check --fix .`, commit (§10) |
| `pytest` — `No module named 'pipeline'` | `src/` layout broken or `packages.find` misconfigured | check `pyproject.toml`; reproduce with a fresh venv |
| `pytest` — `FileNotFoundError: .../sql` or fixture JSON | the file is git-ignored or was never added | `git status --ignored`; check `.gitignore` |
| `pytest` — import error only in CI | **Linux is case-sensitive, Windows isn't**: `from pipeline.Fetch import …` works locally, breaks on the runner | match the real filename exactly |
| `pytest` — a date/timezone assertion | the test depends on "today" or on your local timezone (runner is UTC) | pass the date in explicitly, like `date_window(today=…)` |
| `pytest` — DB connection errors in `ci.yml` | you wrote a DB test without the skip guard | use the `engine` fixture (§6), or mark it (§7) |
| `pipeline.yml` — "Run the full pipeline" fails at fetch | the live API is down, rate-limiting, or changed shape | check the log's HTTP status; rerun (idempotent = safe); if the shape changed, that's the smoke detector doing its job |
| `pipeline.yml` — `connection refused` on 5432 | the Postgres service wasn't ready | that's what the `--health-cmd` block prevents — check it's intact |
| Workflow never appears / never runs | invalid YAML, wrong folder, not on the default branch, or Actions not enabled | §12 and §15 gotchas 3–5 |

**The reproduce-it-locally trick.** If you can't see it, recreate the runner's conditions: a fresh
virtual environment and a clean clone.

```bash
git clone <your-repo> clean-check     # a clone has ONLY committed files - like the runner sees
cd clean-check
python -m venv .venv
.venv\Scripts\activate                # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -e ".[dev]"
ruff check . && pytest -v
```

Nine times out of ten the answer appears in that clone: a file you never committed.

---

# Part D — Doing It

## 18. Hands-On Lab (~45 min, do this before Day 9)

> **Prefer the notebook?** [`17_testing_and_ci_practice.ipynb`](17_testing_and_ci_practice.ipynb)
> covers these drills and more (fixtures, `parametrize`, three graded exercises), with each
> command's output explained right underneath it. This §18 lab is the terminal-only equivalent —
> do either one, not both.

Reading about a smoke detector isn't the same as pressing the test button. Work through these
seven steps in a terminal, in
[`project-nl-open-data-pipeline/`](../../project-nl-open-data-pipeline/). Nothing here changes your
project permanently — the last step of each experiment puts it back.

### Lab 0 — Green baseline (5 min)

```bash
cd module-02-sql-elt-pipeline/project-nl-open-data-pipeline
docker compose -f docker/docker-compose.yml up -d      # the DB, from Week A
pip install -e ".[dev]"                                 # with the module venv ACTIVE
pytest -v
```

**Expect:** `6 passed`. If not, you are in §2's checklist territory — fix it now, not on Day 9.

### Lab 1 — Learn the collection (5 min)

```bash
pytest --collect-only -q          # list every test without running it
pytest tests/test_fetch.py -v     # one file
pytest -k "idempotent" -v         # one test by name fragment
pytest -k "not idempotent" -v     # everything except it
```

Note the `file::test_name` addresses — that's the "node id" you copy from a failure and paste
back to rerun just that test.

### Lab 2 — Break it on purpose, read the scream (10 min)

Open [`src/pipeline/fetch.py`](../../project-nl-open-data-pipeline/src/pipeline/fetch.py) and swap
two values inside `reshape_daily` so the minimum gets the maximum's value:

```python
{"obs_date": d, "temp_max": tmax, "temp_min": tmax, "precip_mm": prec}
#                                            ^^^^ was tmin
```

```bash
pytest -v
```

**Expect:** one `FAILED`, and `E` lines showing `{'temp_min': 22.4} != {'temp_min': 12.1}`.
Read §4 with this real output in front of you: find the `>` line, the diff, the file:line, and
the `short test summary info`. Then restore the file:

```bash
git checkout -- src/pipeline/fetch.py
pytest -q                 # back to green
```

### Lab 3 — Watch a skip happen (5 min)

```bash
docker compose -f docker/docker-compose.yml stop      # take the database away
pytest -v -ra                                         # -ra shows WHY things skipped
```

**Expect:** `4 passed, 2 skipped`, and a summary line quoting
*"No database reachable - start docker compose…"*. This is exactly what happens in `ci.yml` on
every push. Bring it back:

```bash
docker compose -f docker/docker-compose.yml start
pytest -q                 # 6 passed again
```

### Lab 4 — Write a test yourself (10 min)

Add one test to `tests/test_fetch.py`: a single-day window must produce exactly one record whose
date is yesterday. Use Arrange–Act–Assert, and don't let the clock decide anything.

<details>
<summary>💡 Hint</summary>

`date_window` takes `today=` and `days=` — pass both. For the reshape half, build a `daily` dict
with one element in each of the four lists.
</details>

<details>
<summary>✅ Solution</summary>

```python
def test_single_day_window_and_reshape():
    # Arrange
    start, end = date_window(today=date(2026, 7, 17), days=1)
    daily = {
        "time": [end.isoformat()],
        "temperature_2m_max": [24.0],
        "temperature_2m_min": [13.5],
        "precipitation_sum": [0.0],
    }

    # Act
    records = reshape_daily(daily)

    # Assert
    assert start == end == date(2026, 7, 16)          # one day, and it's yesterday
    assert len(records) == 1
    assert records[0]["obs_date"] == "2026-07-16"
    assert records[0]["temp_max"] == 24.0
```

Run it with `pytest -k single_day -v`. Bonus: make it fail on purpose (change `24.0` to `25.0`)
so you've seen your own test work.
</details>

### Lab 5 — Meet the linter (5 min)

Add a useless import at the top of `src/pipeline/load.py`:

```python
import os
```

```bash
ruff check .              # expect: F401 `os` imported but unused
ruff check --fix .        # ruff removes it for you
ruff check .              # "All checks passed!"
git diff                  # confirm the file is back to normal
```

Now you've seen the exact failure that would have turned your first CI run red — and its
one-command fix.

### Lab 6 — Read the workflows like a professional (5 min)

Open both files in [`.github/workflows/`](../../project-nl-open-data-pipeline/.github/workflows/)
and answer these without scrolling back to §13:

1. Which workflow runs when you push a branch, and which one runs at 05:00 UTC?
2. Why does `ci.yml` have no `services:` block, and what happens to the two integration tests
   there?
3. In `pipeline.yml`, what makes `config.py` connect to the CI database instead of the default
   localhost one?
4. Why is `python-version` written as `"3.12"` with quotes?
5. If you wanted to test the nightly workflow right now instead of tomorrow morning, what would
   you click, and what line in the file makes that possible?

<details>
<summary>✅ Answers</summary>

1. `ci.yml` (`on: push, pull_request`); `pipeline.yml` (`on: schedule` with `cron: "0 5 * * *"`).
2. No database is needed for unit tests, so the job stays fast and simple; the `engine` fixture
   can't connect, calls `pytest.skip(...)`, and the two DB tests report as **skipped** — not
   failed.
3. The job-level `env: DATABASE_URL: …`. `config.py` reads `os.environ.get("DATABASE_URL", …)`,
   so the environment wins over the local default — same code, different config.
4. Unquoted, YAML reads `3.10` as the *number* 3.1. Quoting keeps versions as strings.
5. Actions tab → "Scheduled pipeline run" → **Run workflow**. It exists because of the
   `workflow_dispatch:` trigger (and remember: scheduled runs only fire on the default branch).
</details>

### Lab 7 — Leave it clean (2 min)

```bash
git status                # should show no unintended modifications
pytest -q && ruff check . # your new pre-push reflex
```

If `git status` shows changes you didn't mean to keep, `git checkout -- <file>` restores them.

---

## 19. Interview Answers You Now Own

Say these out loud once — they come up in almost every Dutch data/AI engineering interview.

- **"What do you test in a data pipeline?"** — My transformation logic and my contracts, with a
  saved sample of the source response rather than the live API. Above all, idempotency: I have a
  test that runs the load twice and asserts the row count didn't double.
- **"Unit vs integration test?"** — Unit: one function, no infrastructure, milliseconds, runs
  everywhere. Integration: real database, proves the wiring and the SQL. I keep them in separate
  files; the integration ones skip cleanly when no database is reachable, and my scheduled
  workflow runs them against a real Postgres service container.
- **"What is CI and why?"** — A robot running lint and tests on a clean machine on every push, so
  "works on my machine" is caught in a minute instead of in production. Mine is GitHub Actions:
  ruff plus pytest on push and PR.
- **"How do you schedule pipelines?"** — In this project, a GitHub Actions cron workflow with a
  manual dispatch trigger; it runs the pipeline end-to-end against a throwaway Postgres and fails
  loudly. At larger scale you'd use Airflow, Azure Data Factory, or Dagster — same ideas: a
  trigger, isolated runs, logs per step, alerting on failure.
- **"How do you handle secrets?"** — Never in the repo. Environment variables, `.env` locally
  (git-ignored, with a committed `.env.example`), GitHub Actions secrets in CI, Key Vault/app
  settings in Azure. The application code only ever reads the environment.
- **"Your pipeline failed at 05:00. Walk me through it."** — Actions tab, open the red run, find
  the first failing step. The run log names the stage — fetch, load or transform — because each
  logs separately. If it's fetch, check the HTTP status; the pipeline is idempotent, so I can
  simply rerun, and the overlapping 7-day window backfills whatever the failed run missed.

---

## 20. Summary

**Testing**
- Tests are smoke detectors: the payoff is fearless change later, not bug-hunting today
- `pip install -e ".[dev]"` is what makes `import pipeline` work — most pytest pain is this
- `test_*.py` → `test_*` functions → `assert`; Arrange, Act, Assert; one behaviour per test
- Read failures bottom-up: summary → `>` line → `E` diff → file:line. `FAILED` = wrong logic,
  `ERROR` = broken setup
- Flags that matter: `-v -q -x -k --lf --tb=short -s -ra`, and `file.py::test_name`
- Fixtures = *mise en place*; `conftest.py` shares them; `yield` adds teardown; `scope=` controls
  how often
- Unit (fast, no infra) vs integration (real Postgres, skips politely); test *your* logic and
  contracts, never the live API
- `pytest.approx` for floats, `Decimal` from Postgres numerics, `parametrize` for many cases,
  `pytest.raises` for error paths

**Quality gate**
- `ruff check .` is the step most likely to make your first CI run red; `ruff check --fix .`
  clears most of it. Run `ruff check . && pytest -v` before every push

**CI**
- Workflow → event → job → runner → steps (`uses:` a published Action, or `run:` a shell command)
- YAML: two spaces, no tabs, `- ` for lists, quote `"3.12"` and `"0 5 * * *"`
- `ci.yml` = bouncer on every push; `pipeline.yml` = night shift on cron with a Postgres
  **service container**, a health check, and `env: DATABASE_URL` overriding config
- Secrets never enter the repo: `.env` locally, `${{ secrets.X }}` in Actions
- cron is UTC, may be delayed, runs only on the default branch, and sleeps after ~60 quiet days —
  always add `workflow_dispatch`
- The badge in your README is the visible proof that all of this is real

**Next (Days 9–10):** open
[`project-nl-open-data-pipeline/PROJECT_GUIDE.md`](../../project-nl-open-data-pipeline/PROJECT_GUIDE.md)
and build the real thing — everything from Days 6–8 assembled into your first portfolio project.
You now have every piece its milestones assume: §5 for Milestone 2, §9 for Milestones 3–4, and
§14–16 for publishing with a green badge.
