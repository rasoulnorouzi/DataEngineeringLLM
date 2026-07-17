# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**DataEngineeringLLM** is a self-paced, **project-based curriculum** for becoming a professional
**AI engineer** (target: Dutch job market, Azure-centric). The course has 7 modules over ~15 weeks
(~10 hrs/week). Every module produces a **CV-worthy portfolio artifact** — a deployed app or a
self-contained project repo with green CI — built on top of theory lessons and notebooks.

**The single source of truth for the curriculum, progress, and authoring order is [`PLAN.md`](PLAN.md).**
Read it first in every session that touches course content.

This is an educational content repository, not a production application. Your role is to author,
maintain, and improve curriculum materials and project scaffolds.

---

## Weekly-Delivery Workflow (IMPORTANT)

Course content is authored **incrementally, one week at a time, on the learner's request**:

1. The user asks for the next week of content (e.g., "give me next week", "author module 3 week A").
2. Read `PLAN.md` → Progress Tracker → find the next ⬜ week and its scope.
3. Author that week: theory docs + notebooks + exercises + the project milestone for that week,
   following the pedagogy and structure conventions below.
4. Update `PLAN.md`: mark the week 📗 (authored), add a Session Log row, and record any plan changes.
5. Commit with a message referencing the module/week (e.g., "Module 3 week A: FastAPI fundamentals").

When the user reports having *learned* a week, update its Learned column (⬜ → ✅) in `PLAN.md`.
If the plan itself changes (reorder, cut, add), edit `PLAN.md` first, then affected module READMEs.

---

## Repository Structure

```
DataEngineeringLLM/
├── README.md                    # Learner-facing overview & roadmap
├── CLAUDE.md                    # This file (conventions for Claude)
├── PLAN.md                      # Master plan + progress tracker + session log
├── docs/                        # Shared guides
│   ├── DOCKER_GUIDE.md          # Docker from zero (originated in old Week 2)
│   ├── GIT_GITHUB_GUIDE.md      # Git/GitHub workflow
│   ├── AZURE_SETUP_GUIDE.md     # (authored with Module 3)
│   └── LLM_BUDGET_GUIDE.md      # (authored with Module 4)
├── module-01-python-foundations/    # was week1-python-for-data
├── module-02-sql-elt-pipeline/      # was week2-sql-databases
├── module-03-fastapi-azure/
├── module-04-llm-engineering/
├── module-05-rag-pgvector/
├── module-06-agents-langgraph/
└── module-07-capstone/
```

Each module folder follows this template:

```
module-0X-<topic>/
├── README.md            # THE ROUTE: ordered checkbox path through the module (see below)
├── lessons/             # NN_theory_*.md + NN_*_practice.ipynb, numbered in learning order
├── exercises/           # extra practice notebooks with collapsible solutions
└── project-<name>/      # the portfolio artifact — see Project Conventions below
```

**Module README = a route, not an overview (IMPORTANT).** The learner must never wonder "where
do I start, what's next?". Every module README contains a "🧭 Your Route" section: an ordered
checkbox list where every step links the exact file to open, in order (Step 0 setup with a
checkpoint → per-day: read theory X → run notebook Y → do exercise Z → project via its guide),
ending with a "Definition of Done" checklist. `module-02-sql-elt-pipeline/README.md` is the
reference example.

**Every project ships two docs with distinct audiences:**
- `PROJECT_GUIDE.md` — **for the learner**: what the project is in plain words, how to run it
  (with expected output), architecture + one-record data-flow trace, file-by-file code
  walkthrough, design-decision rationale, a transferable "recipe" for building a similar project
  from scratch, the milestones (with collapsible hints/solutions), and a troubleshooting table.
  `project-nl-open-data-pipeline/PROJECT_GUIDE.md` is the reference example.
- `README.md` — **for recruiters/visitors** when the folder is published as a standalone repo:
  short pitch, architecture, quickstart, layout. Links to the guide for course learners.

---

## Project Conventions (the portfolio artifacts)

Each `project-*/` folder must be **self-contained** so the learner can copy it out as a standalone
public GitHub repo — that repo with its green CI badge is the CV artifact. Self-contained means:

- Own `pyproject.toml` (or `requirements.txt`), own `README.md` with setup + architecture
- Own `tests/` runnable with plain `pytest`
- Own `Dockerfile` and/or `docker/docker-compose.yml` where relevant — `docker compose up` must work
- Own `.github/workflows/*.yml` (these run when the folder is copied out to its own repo;
  inside this monorepo they serve as reference/teaching material unless path-filtered)
- No imports from `lessons/` or other modules — duplication into the project folder is fine and intentional
- Secrets via `.env` (git-ignored) + `.env.example` committed

Cost guardrails: LLM-calling projects default to cheap models (gpt-4o-mini / Claude Haiku class)
with an Ollama fallback path; total course API budget is €10–20.

---

## Pedagogy Rules (unchanged from v1 — keep these)

- **Theory first**: each topic starts with a `NN_theory_*.md` explaining *why* the concept exists
  before *how* to use it. Use analogies and "bad way vs good way" comparisons.
- **Learning by doing**: notebooks guide through worked examples before independent exercises.
- **Progressive complexity**: simple → complex within each week; each module's project composes
  skills from earlier modules.
- **Beginner-friendly language**: assume no prior knowledge of the week's topic; explain jargon on
  first use; audience is beginner-to-intermediate.
- **Exercises**: 2–3 difficulty levels where possible, collapsible solutions (`<details>` blocks),
  solutions tested before committing.
- **Notebooks**: clear outputs before committing (except `*_executed.ipynb` reference copies);
  test in a fresh kernel for reproducibility.
- When explaining concepts, **reuse the analogies already present in the materials** — consistency
  matters for students.

---

## Common Commands

### Module environment setup (each module is independent)

```bash
cd module-0X-<topic>
python -m venv .venv
.venv\Scripts\activate            # Windows (this repo's primary OS)
pip install -r requirements.txt
```

### Module 2 database stack

```bash
cd module-02-sql-elt-pipeline/project-nl-open-data-pipeline
docker compose -f docker/docker-compose.yml up -d
docker ps                          # verify
docker compose -f docker/docker-compose.yml down
```

Access: pgAdmin http://localhost:8080 (`student@example.com` / `admin`);
PostgreSQL localhost:5432, db `week2_db`, user `student`, password `student123`.

### Tests

```bash
cd module-0X-<topic>/project-<name>
pytest -v
```

---

## Environment

- **Python** 3.10+ (tested on 3.13); one `.venv` per module
- **OS**: Windows 11 (commands in docs should show Windows first, Linux/Mac alternative second)
- **Docker Desktop** required from Module 2 onward
- **Azure** free tier from Module 3 onward (Container Apps, Container Registry)
- **LLM APIs** from Module 4 onward (OpenAI/Anthropic keys via `.env`; Ollama for free local dev)

---

## Git & Version Control

- `main` holds stable, tested materials
- Notebooks committed with outputs cleared (except `*_executed.ipynb`)
- `.venv/`, Docker volumes, `.env`, and generated output artifacts are git-ignored
- Commit messages reference module + topic: "Module 3 week A: FastAPI fundamentals"

---

## Notes for Claude Code

- **Educational clarity beats code elegance.** "Refactor" means improve learning outcomes.
- Follow existing patterns for structure and pedagogy when extending the curriculum.
- Never author ahead of the tracker without being asked — the weekly-delivery model is deliberate
  (it keeps content aligned with the learner's actual progress and lets the plan adapt).
- Verification is manual/interactive: run notebooks in a fresh kernel, `docker compose up`,
  `pytest` in project folders. No global automated test suite.
