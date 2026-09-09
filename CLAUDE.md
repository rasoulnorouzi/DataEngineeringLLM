# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**DataEngineeringLLM** is a self-paced, **project-based curriculum** for becoming a professional
**AI engineer** (target: Dutch job market, Azure-centric). 7 modules over ~15 weeks (~10 hrs/week).
Every module produces a **CV-worthy portfolio artifact** — a self-contained project repo with green
CI — built on top of theory lessons and notebooks.

**The single source of truth for the curriculum, progress, and authoring order is [`PLAN.md`](PLAN.md).**
Read it first in every session that touches course content.

This is an educational content repository, not a production application. Your role is to author,
maintain, and improve curriculum materials and project scaffolds.

---

## Weekly-Delivery Workflow (IMPORTANT)

Course content is authored **incrementally, one week at a time, on the learner's request**:

1. The user asks for the next week of content ("give me next week", "author module 3 week A").
2. Read `PLAN.md` → Progress Tracker → find the next ⬜ week and its scope.
3. Author that week: theory docs + notebooks + exercises + the project milestone for that week.
4. Update `PLAN.md`: mark the week 📗 (authored), add a Session Log row, record any plan changes.
5. Commit referencing module + topic (e.g. "Module 3 week A: FastAPI fundamentals").

When the user reports having *learned* a week, update its Learned column (⬜ → ✅) in `PLAN.md`.
If the plan itself changes (reorder, cut, add), edit `PLAN.md` first, then affected module READMEs.

**Never author ahead of the tracker without being asked** — the weekly model is deliberate: it keeps
content aligned with actual progress and lets the plan adapt.

Current state (verify against `PLAN.md`, it moves): Modules 1–2 authored, Module 3 is next.
Modules 3–7 are README stubs only. `docs/AZURE_SETUP_GUIDE.md` and `docs/LLM_BUDGET_GUIDE.md` are
stubs to be authored *with* Modules 3 and 4 respectively.

---

## Structure Conventions

```
module-0X-<topic>/
├── README.md            # THE ROUTE (see below)
├── lessons/             # NN_theory_*.md + NN_*_practice.ipynb, numbered in learning order
├── exercises/           # extra practice notebooks with collapsible solutions
└── project-<name>/      # the portfolio artifact
```

**Module README = a route, not an overview.** The learner must never wonder "where do I start,
what's next?". Every module README has a "🧭 Your Route" section: an ordered checkbox list where
each step links the exact file to open (Step 0 setup with a checkpoint → per-day: read theory X →
run notebook Y → do exercise Z → project via its guide), ending with a "Definition of Done"
checklist. `module-02-sql-elt-pipeline/README.md` is the reference example — Module 1's README does
*not* yet follow it (retrofit item).

**Lesson numbering is module-global, not folder-local.** Module 2 runs `01_`→`17_` continuously
across the `dayN-*/` folders. New lessons continue the sequence.

**Every project ships two docs with distinct audiences:**
- `PROJECT_GUIDE.md` — **for the learner**: what it is in plain words, how to run it with expected
  output, architecture + one-record data-flow trace, file-by-file walkthrough, design rationale, a
  transferable "recipe", milestones with collapsible hints, troubleshooting table.
  `project-nl-open-data-pipeline/PROJECT_GUIDE.md` is the reference example.
- `README.md` — **for recruiters/visitors** when the folder is published standalone: short pitch,
  architecture, quickstart, layout.

**Each `project-*/` folder is self-contained** so the learner can copy it out as a standalone public
repo — that repo with its green CI badge is the CV artifact. Own `pyproject.toml`, own `tests/`
runnable with plain `pytest`, own `Dockerfile`/`docker/docker-compose.yml` where relevant, own
`.github/workflows/`, `.env.example` committed and `.env` git-ignored. **No imports from `lessons/`
or other modules** — duplicating code into the project folder is intentional.

Cost guardrails: LLM-calling projects default to cheap models (gpt-4o-mini / Claude Haiku class)
with an Ollama fallback path; total course API budget is €10–20.

---

## Architecture: `nl-open-data-pipeline` (Module 2)

The only working project so far, and the template every later project imitates. Reading one file
does not explain it:

- **One Postgres serves everything.** `docker/init.sql` seeds a `company` schema (departments,
  employees, products, sales, deliberately containing NULLs, salary ties and an unsold product for
  JOIN/RANK demos) — that is the dataset **every SQL lesson notebook and exercise** queries. The
  pipeline then creates `raw`/`staging`/`marts` in the *same* database. So `docker compose up` in
  the project folder is a prerequisite for the module's lessons, not just the project.
- **Legacy names are load-bearing.** `week2_db`, `week2_postgres`, `student`/`student123` predate
  the module layout but are hardcoded across lesson notebooks, guides, `.env.example`, and both
  workflows. Renaming is a multi-file change; don't do it casually.
- **Flow.** `run.py` orchestrates fetch → load → transform. `fetch.py` pulls a rolling 7-day window
  *ending yesterday* (today's archive data is incomplete) for 6 Dutch cities from Open-Meteo.
  `load.py` upserts into `raw.weather_daily` with `ON CONFLICT (city, obs_date) DO UPDATE` — that
  upsert **is** the idempotency lesson the whole project exists to teach, and Milestone 2 verifies
  it. `transform.py` executes every `sql/*.sql` file in **sorted filename order**, so the `10_`/
  `20_` prefixes are ordering, not decoration; staging and marts DROP-and-rebuild each run while
  raw only ever accumulates.
- **`SQL_DIR` is path-derived.** `transform.py` walks three parents up to reach `<project>/sql`.
  Moving `src/pipeline/` silently breaks transforms.
- **Test split.** Unit tests use the saved fixture `tests/fixtures/open_meteo_sample.json` and never
  call the live API. Integration tests `pytest.skip` when no database is reachable — so a green
  local `pytest` does **not** prove the database path works. `pipeline.yml` is where that path is
  really exercised.
- **Two workflows, two jobs.** `ci.yml` = lint + tests on every push/PR. `pipeline.yml` = daily cron
  05:00 UTC plus manual dispatch, runs the full pipeline against a throwaway Postgres service
  container using the live API, then runs only `tests/test_db_integration.py`.
- **The ruff rule set is pinned on purpose** (`select = ["E","W","F","I","B","UP"]` in
  `pyproject.toml`): ruff's defaults grow with releases and an upstream rule should never redden CI
  without a code change. Day 8 teaches this. Don't "simplify" it away.

---

## Common Commands

### Module environment (each module is independent)

```bash
cd module-0X-<topic>
python -m venv .venv
source .venv/bin/activate          # Linux/Mac   (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

### Module 2 database stack (needed by lessons *and* project)

```bash
cd module-02-sql-elt-pipeline/project-nl-open-data-pipeline
docker compose -f docker/docker-compose.yml up -d
docker ps                          # expect week2_postgres (healthy) + week2_pgadmin
docker compose -f docker/docker-compose.yml down          # add -v to wipe the volume and reseed
```

pgAdmin http://localhost:8080 (`student@example.com` / `admin`);
Postgres localhost:5432, db `week2_db`, user `student`, password `student123`.

### Working on a project folder

```bash
cd module-0X-<topic>/project-<name>
pip install -e ".[dev]"            # REQUIRED: src layout — tests import `pipeline`, not a path
python -m pipeline.run             # run the pipeline end-to-end
ruff check .                       # CI gate; --fix to autofix
pytest -v                          # 6 tests; integration ones skip without a database
pytest tests/test_fetch.py::test_reshape_daily -v      # single test
pytest -k "idempoten" -v                               # by name substring
```

### Executing a notebook headlessly (verify it runs top-to-bottom)

```bash
cd module-0X-<topic>
.venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace lessons/<path>/<name>.ipynb
```

Requires the module's stack to be up first (e.g. Module 2's Postgres containers).

---

## Pedagogy Rules

- **Theory first**: each topic starts with a `NN_theory_*.md` explaining *why* the concept exists
  before *how* to use it. Analogies and "bad way vs good way" comparisons.
- **A bridge/theory lesson must cover every skill its project's milestones assume.** This rule came
  from learner feedback (Day 8 was too thin to actually do the project) — apply it to every module.
- **Explain every token of syntax (learner feedback, 2026-09-08).** Earlier modules skipped detail,
  especially SQL syntax. The first time a construct appears, break it down piece by piece — what
  each keyword, symbol, clause and argument does and why it is there. Annotate real snippets line by
  line. No unexplained magic, no "as you can see".
- **Design for recall, not just comprehension (learner feedback, 2026-09-08).** Earlier material was
  understandable but forgettable. Every lesson carries retrieval scaffolding: a memorable
  analogy/mnemonic per concept, a one-line "remember this" takeaway box, **active-recall questions
  asked before the answer is shown**, a short spaced-review block that re-tests earlier days, and a
  module cheat sheet the learner can keep. Prefer making the learner produce the answer over showing
  it to them.
- **A demo must be executed and its output *read* before shipping.** "It runs without erroring" is
  not the same as "it demonstrates the claim". Three Module 3 demos ran clean while showing the
  opposite of what the prose said (see the 2026-09-08 Session Log entry in `PLAN.md`).
- **Learning by doing**: notebooks walk through worked examples before independent exercises.
- **Progressive complexity**: simple → complex within each week; each project composes earlier skills.
- **Beginner-friendly language**: assume no prior knowledge of the week's topic; explain jargon on
  first use; audience is beginner-to-intermediate.
- **Exercises**: 2–3 difficulty levels where possible, collapsible `<details>` solutions, solutions
  tested before committing.
- **Reuse the analogies already in the materials** (raw = "evidence locker", idempotency = "light
  switch", CI = "the bouncer", scheduled run = "the night shift") — consistency matters.

---

## Notebook Gotchas

- In SQL lesson notebooks the `run_query` helper (built on `pd.read_sql_query`) is **SELECT-only** —
  it crashes on statements returning no rows. DDL/DML (CREATE/DROP/INSERT/UPDATE) must go through a
  committing `run_command` helper; `10_indexing_practice.ipynb` defines both plus `run_explain`.
- Notebooks that create database objects need an **idempotent reset cell** at the top so they re-run
  cleanly.
- **Output policy is not uniform, and differs per module.** Module 2's lesson practice notebooks
  (Days 1–7) and `01_python_for_data_executed.ipynb` are committed **with** outputs, so learners can
  read expected results without a live database; its exercises and `17_testing_and_ci_practice.ipynb`
  are **cleared**. **All of Module 3 is cleared** — its notebooks are self-contained enough to run
  anywhere, and several are timing or failure demos whose stale output would mislead. Match the
  neighbouring files; don't mass-clear or mass-execute across a module boundary.
- Test in a fresh kernel before committing.

---

## Environment

- **Python** 3.10+ (this machine: 3.13.5); one `.venv` per module. `myenv/` at the repo root is a
  git-ignored scratch venv.
- **OS**: the current dev machine is Linux (Debian, Docker CLI available). Existing course docs are
  written **Windows-first** (`.venv\Scripts\activate` first, Linux/Mac second) — keep that ordering
  in learner-facing docs unless the user says otherwise.
- **Docker** required from Module 2 onward; **Azure** free tier from Module 3; **LLM APIs** from
  Module 4 (`.env` keys, Ollama for free local dev).

---

## Git

- `main` holds stable, tested materials.
- `.venv/`, `myenv/`, `.env`, `__pycache__/`, caches, and generated `data_output/` are git-ignored,
  as are the Day 5 regenerated `data/` files and the Day 8 `sandbox/`.
- Commit messages reference module + topic ("Module 3 week A: FastAPI fundamentals"). Recent history
  contains generic auto-generated messages — do not imitate those.

---

## Notes for Claude Code

- **Educational clarity beats code elegance.** "Refactor" means improve learning outcomes.
- Follow existing patterns for structure and pedagogy when extending the curriculum.
- Verification is manual/interactive: run notebooks in a fresh kernel, `docker compose up`, `pytest`
  and `ruff check .` in project folders. There is no global automated test suite.
