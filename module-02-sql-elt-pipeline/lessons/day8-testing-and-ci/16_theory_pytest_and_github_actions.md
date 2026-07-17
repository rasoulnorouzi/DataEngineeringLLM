# Day 8 Theory (Bridge Lesson): pytest & GitHub Actions — Your Safety Net

**Time:** ~2 hours reading + trying commands
**Prerequisites:** Day 7. Also skim [docs/GIT_GITHUB_GUIDE.md](../../../docs/GIT_GITHUB_GUIDE.md)
if Git/GitHub still feels shaky.

> **Why "bridge" lesson?** Testing and CI formally belong to Module 1's project layer, but your
> pipeline project needs them *now*. This is the from-zero version; Module 1's `datacli` project
> will deepen it.

---

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

---

## 2. pytest in Ten Minutes

pytest is Python's de-facto testing tool. The rules are almost embarrassingly simple:

1. Test files are named `test_*.py` (usually in a `tests/` folder)
2. Tests are plain functions named `test_*`
3. Inside, you `assert` things
4. Run `pytest` — it finds and runs everything, green dot per pass, red F per fail

```python
# src/pipeline/transform_helpers.py  (the code under test)
def reshape_daily(daily: dict) -> list[dict]:
    """Turn Open-Meteo's parallel arrays into one record per day."""
    return [
        {"obs_date": d, "temp_max": tmax, "temp_min": tmin, "precip_mm": prec}
        for d, tmax, tmin, prec in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_sum"],
        )
    ]
```

```python
# tests/test_reshape.py
from pipeline.transform_helpers import reshape_daily


def test_reshape_pairs_values_by_position():
    daily = {
        "time": ["2026-07-01", "2026-07-02"],
        "temperature_2m_max": [22.4, 19.8],
        "temperature_2m_min": [12.1, 11.3],
        "precipitation_sum": [0.0, 4.2],
    }

    records = reshape_daily(daily)

    assert len(records) == 2
    assert records[0] == {
        "obs_date": "2026-07-01", "temp_max": 22.4, "temp_min": 12.1, "precip_mm": 0.0,
    }


def test_reshape_empty_input_gives_empty_list():
    daily = {"time": [], "temperature_2m_max": [],
             "temperature_2m_min": [], "precipitation_sum": []}
    assert reshape_daily(daily) == []
```

```bash
pytest -v          # verbose: one line per test
```

### The pattern behind every good test: Arrange–Act–Assert

1. **Arrange** — build the input (a small fake `daily` dict)
2. **Act** — call the function once
3. **Assert** — check the result

One behavior per test, named after the behavior (`test_reshape_pairs_values_by_position`), so a
failure message reads like a sentence telling you what broke.

### What to test (and what not)

- ✅ **Your logic**: reshaping, filtering, date-window calculation, SQL-building
- ✅ **Edge cases**: empty input, missing values (`None` in the arrays — remember Day 7!)
- ❌ **Not other people's code**: don't test that `requests` works or Postgres can insert
- ❌ **Not the live API in unit tests**: slow, flaky, impolite. Test *your* handling of a
  *saved example response* instead (the project repo ships one as a "fixture")

**Tests involving the database** are called *integration tests* — they're valuable too, and the
project includes some that run against your Docker Postgres (and skip themselves politely when
the database isn't running).

---

## 3. CI: Why a Robot Should Run Your Tests

Tests only protect you if they *run*. Humans forget. So we make a robot run them on **every push**:
that's **Continuous Integration (CI)**.

**Analogy — the bouncer.** `main` is the club: only code that passes the dress code (tests +
linter) gets in. The bouncer never gets tired, never makes exceptions because "it's a tiny
change," and checks *every* guest.

Concretely, with **GitHub Actions** (GitHub's built-in CI service, free for public repos):

1. You push code (or open a pull request)
2. GitHub boots a fresh Linux machine in the cloud
3. It checks out your code, installs dependencies, runs `ruff` (linter) and `pytest`
4. Green ✅ or red ❌ appears on your commit/PR — and on the **badge** in your README

That fresh machine is a feature: if it only works on *your* laptop ("works on my machine!"), CI
exposes it immediately — missing dependency, hardcoded path, forgotten file.

## 4. Reading a Workflow File

Workflows live in `.github/workflows/*.yml`. Here's your project's CI, annotated:

```yaml
name: CI

on:                          # WHEN does this run?
  push:                      #   every push to any branch
  pull_request:              #   and every PR

jobs:
  test:                      # a job = one fresh cloud machine
    runs-on: ubuntu-latest   # which machine (Linux — like most servers)

    steps:                   # steps run in order, top to bottom
      - uses: actions/checkout@v4          # step 1: get your code onto the machine
                                           # ("uses:" = reuse a published building block)
      - uses: actions/setup-python@v5      # step 2: install Python
        with:
          python-version: "3.12"

      - run: pip install -e ".[dev]"       # step 3: install project + dev tools
                                           # ("run:" = a shell command, like you'd type)
      - run: ruff check .                  # step 4: linter (style/bug smells)
      - run: pytest -v                     # step 5: the smoke detectors
```

That's the whole magic: **a YAML file describing the commands you'd run yourself, executed by a
robot on every push.** If any step fails, the run is red and GitHub emails you.

## 5. The Same Robot, on a Timer: `schedule`

Remember Day 6's question — *who presses "run" every night?* The `on:` block has one more trigger:

```yaml
on:
  schedule:
    - cron: "0 5 * * *"      # every day at 05:00 UTC (= 06:00/07:00 in NL)
  workflow_dispatch:          # + a manual "Run workflow" button in the GitHub UI
```

That five-field string is **cron syntax**, the 50-year-old standard for schedules:

```
┌───────── minute        (0)
│ ┌─────── hour          (5)
│ │ ┌───── day of month  (* = every)
│ │ │ ┌─── month         (* = every)
│ │ │ │ ┌─ day of week   (* = every)
0 5 * * *
```

More examples: `0 * * * *` = every hour · `*/15 * * * *` = every 15 min · `0 8 * * 1` = Mondays 08:00.
(Two honest gotchas: times are **UTC**, and GitHub may delay scheduled runs by a few minutes —
fine for us, worth knowing for interviews.)

So your project gets **two** workflows:

- `ci.yml` — bouncer: lint + tests on every push/PR
- `pipeline.yml` — night shift: on a cron schedule, boots a machine, **spins up a temporary
  Postgres, runs your entire pipeline end-to-end against the live API**, and fails loudly if
  anything broke. (A scheduled *smoke run* — the cloud database it fills is thrown away after;
  in Module 3 you'll point it at a persistent Azure database instead.)

Seeing a green scheduled run in your repo's Actions tab every morning is exactly the "automated
nightly runs" claim on your CV — and you can show the run history to prove it.

---

## 6. Summary

- Tests = smoke detectors; their value is fearless change later, not bug-hunting today
- pytest: `test_*.py`, `test_*` functions, `assert`, run `pytest` — Arrange, Act, Assert
- Test **your** logic and edge cases; not libraries, not the live API (use saved fixtures)
- CI = a robot running lint+tests on every push, on a fresh machine (GitHub Actions, YAML file)
- `schedule:` + cron syntax turns the same robot into your pipeline's night-shift operator

**Next (Days 9–10):** open `project-nl-open-data-pipeline/README.md` and build the real thing —
everything from Days 6–8 assembled into your first portfolio project.
