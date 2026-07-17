# AI Engineer Path — Master Plan

> **This file is the single source of truth** for the curriculum, the progress tracker, and the
> weekly-delivery workflow. Claude Code reads this file at the start of every authoring session.

**Goal:** Become a professional AI engineer for the **Dutch job market** through a project-based,
self-paced course. Every module ends with a **CV-worthy portfolio artifact** — a deployed app or a
public repo with green CI — not just notebooks.

**Constraints:**
- Pace: ~10 hrs/week → **15 weeks ≈ 150 hours total**
- Cloud: **Azure** (dominant in NL enterprise — ING, ABN AMRO, government, consultancies)
- LLM API budget: **€10–20 total** (gpt-4o-mini / Claude Haiku class; Ollama local fallback for all iterative dev)
- Everything must run locally with `docker compose up`; Azure deploys use free tiers only

---

## How This Course Is Delivered (Weekly-Delivery Protocol)

Content is authored **incrementally, one week at a time**, on request:

1. **You (the learner) ask:** "give me next week" (or "author module X week Y").
2. **Claude reads this file** — specifically the [Progress Tracker](#progress-tracker) — to find the
   next 🚧/⬜ week and its scope.
3. **Claude authors that week's content** following the module template
   (theory `.md` → hands-on notebook → exercises with collapsible solutions → project milestone),
   consistent with the pedagogy rules in `CLAUDE.md`.
4. **Claude updates the Progress Tracker** below (⬜ → ✅ for authored, and marks your learning
   progress when you report it) and commits.

If the plan needs changing (reorder modules, cut/add a topic), change **this file first**, then the
affected module READMEs.

---

## Curriculum Overview

| # | Module | Weeks | Portfolio project | Core stack |
|---|--------|-------|-------------------|------------|
| 1 | Professional Python & Engineering Habits | 2 | **`datacli`** — typed, tested, installable CSV-cleaning CLI with green CI badge | Python 3.12, Pydantic, Typer, pytest, ruff, GitHub Actions |
| 2 | SQL, Docker & a Scheduled ELT Pipeline | 2 | **`nl-open-data-pipeline`** — scheduled ingest of Dutch open data (KNMI weather) into Dockerized Postgres, layered SQL (raw→staging→marts), DuckDB analytics | PostgreSQL 16, SQLAlchemy, DuckDB, GitHub Actions cron, pytest |
| 3 | FastAPI, CI/CD & First Azure Deploy | 2 | **`insight-api`** — containerized FastAPI service over Module 2 data, auto-deployed to Azure Container Apps, live OpenAPI docs | FastAPI, Docker, GitHub Actions CD, Azure Container Apps |
| 4 | LLM Engineering Fundamentals | 2 | **`doc-extract`** — LLM document→validated-JSON extraction service with a pytest eval suite in CI and provider fallback (API ↔ Ollama) (~€3) | OpenAI/Anthropic SDK, Pydantic, Ollama, pytest evals |
| 5 | RAG & Vector Databases | 2 | **`ask-my-docs`** — RAG API over pgvector with source-cited answers + retrieval eval report (recall@k), Azure deployed (~€4) | pgvector, embeddings, FastAPI, pytest |
| 6 | Agents & Tool Harnessing | 2 | **`data-analyst-agent`** — natural-language questions over the Module 2 DB; raw agent loop from scratch, then LangGraph (tools: `run_sql`, `search_docs`, `plot_chart`) (~€5) | LangGraph, OpenAI/Anthropic SDK, FastAPI |
| 7 | Capstone: `knowledge-copilot` | 3 | **"Ask HR"** company knowledge assistant: RAG + agent SQL tool + citations, chat UI, Langfuse tracing, evals in CI, CD to Azure (~€6) | Everything above, composed |

Total: **15 weeks / ~150 hrs / ~€18 API spend.**

### Module details & CV bullets

**M1 — Professional Python & Engineering Habits.** Type hints, dataclasses/Pydantic, pandas/numpy,
pathlib, logging (existing Week-1 material) + new: `pyproject.toml` packaging, git/GitHub workflow,
pytest, ruff, first CI workflow.
> *CV: "Built and published a tested, typed Python CLI for data validation and transformation with automated linting and testing via GitHub Actions CI."*

**M2 — SQL, Docker & a Scheduled ELT Pipeline.** All Week-2 SQL (joins, CTEs, window functions,
indexing, DuckDB) + new: ELT concepts, idempotent & incremental loads, raw/staging/marts layering,
dbt-in-concept lesson, scheduling with GitHub Actions cron, pytest + CI bridge lesson.
> *CV: "Designed a scheduled ELT pipeline ingesting Dutch open-government data into Dockerized PostgreSQL with layered SQL transformations and automated nightly runs."*

**M3 — FastAPI, CI/CD & First Azure Deploy.** HTTP/REST from zero, FastAPI + Pydantic models,
dependency injection, async basics, API testing (TestClient/httpx), production Dockerfile,
CI build+push, CD to Azure Container Apps, secrets/env management.
> *CV: "Developed and deployed a containerized FastAPI analytics service to Azure Container Apps with a full CI/CD pipeline (test, build, deploy on merge)."*

**M4 — LLM Engineering Fundamentals.** How LLMs work (tokens, context, temperature), calling
OpenAI/Anthropic APIs, structured outputs, tool/function calling, prompt versioning, evals with
pytest (golden sets, LLM-as-judge), cost control, provider abstraction with Ollama fallback.
> *CV: "Built an LLM-powered document extraction service with structured outputs, an automated evaluation suite in CI, and multi-provider fallback (OpenAI/Ollama) for cost control."*

**M5 — RAG & Vector Databases.** Embeddings intuition, chunking strategies, pgvector (Postgres
extension — builds on M2!), similarity + hybrid search, retrieval evaluation (recall@k,
faithfulness), citations/grounding, failure modes of RAG.
> *CV: "Implemented a production-style RAG system with pgvector, chunking and hybrid retrieval, source-cited answers, and measured retrieval quality (recall@k)."*

**M6 — Agents & Tool Harnessing.** Agent loop built from scratch with raw tool-calling first
(demystification), then LangGraph: state, nodes, edges, conditional routing, human-in-the-loop,
memory; tool design, error handling, guardrails, tracing.
> *CV: "Engineered a multi-tool LLM agent with LangGraph (SQL querying, document retrieval, self-correction loops) exposed via a FastAPI service."*

**M7 — Capstone `knowledge-copilot`.** Week 1: ingestion + RAG core + FastAPI. Week 2: LangGraph
routing (RAG vs SQL vs refuse/clarify), guardrails, minimal chat UI. Week 3: hardening — evals in
CI, Langfuse tracing, cost caps, CD to Azure, architecture diagram + demo GIF in README.
> *CV: "Shipped an end-to-end AI knowledge assistant (RAG + agents + FastAPI) to Azure with CI/CD, tracing, evals, and LLM cost guardrails."*

---

## What Was Cut From the Original Plan (and why)

| Original topic | Decision | Why |
|---|---|---|
| Apache Airflow | **Cut** → GitHub Actions cron + plain Python orchestration | NL AI-engineer postings rarely require it; setup burns hours teaching DAG syntax, not concepts. Scheduling concepts transfer. |
| Snowflake & BigQuery | **Cut** → DuckDB + Azure Postgres | Need accounts/credit cards, not free long-term; wrong target role. DuckDB teaches the same columnar/analytics concepts free. |
| dbt (full week) | **Shrunk** → 2-hr concepts lesson in M2 | Layered SQL transformations taught hands-on without dbt; full dbt depth is an analytics-engineer skill. |
| Standalone "Data Pipelines & ETL" week | **Merged** into M2 | Half a week of content once SQL + Docker exist. |
| Kubernetes | **Out** | Azure Container Apps abstracts it; rabbit hole for a solo learner. |
| Heavy MLOps (MLflow, model training) | **Shrunk** → evals + tracing + CI/CD in M4/M7 | For LLM apps, "MLOps basics" means evals, tracing, cost monitoring — all covered. |

---

## Repo Layout

```
DataEngineeringLLM/
├── README.md / CLAUDE.md / PLAN.md (this file)
├── docs/                       # shared guides (Docker, Git, Azure, LLM budget)
├── module-0X-<topic>/
│   ├── README.md               # goals, schedule, project one-pager
│   ├── lessons/                # theory .md + notebooks
│   ├── exercises/
│   └── project-<name>/         # SELF-CONTAINED: own pyproject.toml, tests/, Dockerfile,
│                               # .github/workflows/ — copyable out as a standalone public repo
└── module-07-capstone/
```

**Key conventions:**
- Each `project-*/` folder is self-contained so the learner can copy it out as a standalone
  public GitHub repo with a green CI badge — that repo is the CV artifact.
- Every module README is a **route**: an ordered checkbox path naming the exact file for every
  step (no "where do I start?" ever). Reference: `module-02-sql-elt-pipeline/README.md`.
- Every project ships a learner-facing **`PROJECT_GUIDE.md`** (run steps, architecture, code
  walkthrough, design rationale, build-it-yourself recipe, milestones, troubleshooting) next to
  the recruiter-facing `README.md`. Reference: `project-nl-open-data-pipeline/PROJECT_GUIDE.md`.

---

## Progress Tracker

Legend: ✅ authored & learned · 📗 authored, not yet learned · 🚧 authoring in progress · ⬜ not authored

| Module / week | Authored | Learned | Notes |
|---|---|---|---|
| M1 wk1–2 lessons (Python foundations) | ✅ (as old Week 1) | ✅ | Lessons live in `module-01-python-foundations/lessons/`; notebook split + polish = retrofit, low priority |
| M1 `datacli` project + pytest/ruff/CI lessons | ⬜ | ⬜ | Retrofit session; pytest+CI basics pulled forward into M2 bridge lesson |
| M2 wk A (SQL lessons day1–5, adapted) | 📗 | ⬜ | Old Week-2 lessons, de-referenced from Airflow/dbt/Snowflake |
| M2 wk B (ELT, ingestion, scheduling, bridge lesson) | 📗 | ⬜ | Authored 2026-07-17 |
| M2 project `nl-open-data-pipeline` scaffold | 📗 | ⬜ | KNMI ingestion, layered SQL, tests, cron workflow |
| M3 wk A (FastAPI fundamentals) | ⬜ | ⬜ | Next authoring target after M2 is learned |
| M3 wk B (Docker→Azure CD, `insight-api`) | ⬜ | ⬜ | Author `docs/AZURE_SETUP_GUIDE.md` with this |
| M4 wk A (LLM APIs, structured outputs) | ⬜ | ⬜ | Author `docs/LLM_BUDGET_GUIDE.md` with this |
| M4 wk B (evals, provider fallback, `doc-extract`) | ⬜ | ⬜ | |
| M5 wk A (embeddings, pgvector) | ⬜ | ⬜ | |
| M5 wk B (retrieval eval, `ask-my-docs`) | ⬜ | ⬜ | |
| M6 wk A (raw agent loop, tool design) | ⬜ | ⬜ | |
| M6 wk B (LangGraph, `data-analyst-agent`) | ⬜ | ⬜ | |
| M7 capstone spec + 3 weekly milestones | ⬜ | ⬜ | Author last, once patterns are stable |

**Authoring order:** M2 ✅ → M3 → M4 → M5 → M6 → M1 retrofit → M7.
(M1 retrofit is light — file moves are done; only `datacli` project + formalized testing/CI lessons remain.)

---

## Session Log

| Date | What was authored / changed |
|---|---|
| 2026-07-17 | Restructured repo to module layout; wrote PLAN.md, new README/CLAUDE.md, module skeletons; authored Module 2 (adapted SQL lessons + Week B ELT/scheduling content + `nl-open-data-pipeline` project scaffold). |
| 2026-07-18 | Learner feedback: Module 2 confusing, no clear order. New conventions (all future modules): module README = ordered checkbox route; every project gets learner-facing PROJECT_GUIDE.md (run steps, code walkthrough, recipe, milestones). Applied both to Module 2. |
