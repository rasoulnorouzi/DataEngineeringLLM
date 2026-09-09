# AI Engineer Path

A self-paced, **project-based** course to go from Python basics to **professional AI engineer**,
tuned for the Dutch job market (Azure-centric). Every module ends with a **portfolio project** you
can show in interviews: a deployed API, a scheduled pipeline, a RAG system, an LLM agent — each one
a self-contained repo with tests and CI.

> 📋 Curriculum details, progress tracking, and the authoring plan live in [PLAN.md](PLAN.md).

---

## 🗺️ Roadmap (7 modules, ~15 weeks @ ~10 hrs/week)

| # | Module | Weeks | Portfolio project | Status |
|---|--------|-------|-------------------|--------|
| 1 | [Professional Python & Engineering Habits](module-01-python-foundations/README.md) | 2 | `datacli` — typed, tested CSV-cleaning CLI with CI badge | 📗 Lessons ready (project TBD) |
| 2 | [SQL, Docker & a Scheduled ELT Pipeline](module-02-sql-elt-pipeline/README.md) | 2 | `nl-open-data-pipeline` — scheduled Dutch open-data ingest → Postgres → layered SQL → DuckDB analytics | ✅ Done |
| 3 | [FastAPI, CI/CD & First Azure Deploy](module-03-fastapi-azure/README.md) | 2 | `insight-api` — containerized FastAPI service, CD to Azure Container Apps | 📗 Ready |
| 4 | [LLM Engineering Fundamentals](module-04-llm-engineering/README.md) | 2 | `doc-extract` — LLM document→JSON extraction with eval suite in CI | ⬜ Planned |
| 5 | [RAG & Vector Databases](module-05-rag-pgvector/README.md) | 2 | `ask-my-docs` — RAG API over pgvector with cited answers + retrieval evals | ⬜ Planned |
| 6 | [Agents & Tool Harnessing](module-06-agents-langgraph/README.md) | 2 | `data-analyst-agent` — LangGraph agent answering NL questions over a real DB | ⬜ Planned |
| 7 | [Capstone: `knowledge-copilot`](module-07-capstone/README.md) | 3 | "Ask HR" knowledge assistant — RAG + agents + FastAPI + CI/CD + Azure | ⬜ Planned |

**What you can do at the end:** build and deploy LLM-powered products end-to-end — FastAPI services,
RAG systems, multi-tool agents — with tests, evals, CI/CD, Docker, and Azure. These map directly to
NL AI-engineer job postings.

---

## 🚀 How This Course Works

1. **Work modules in order.** Each module composes skills from earlier ones (the agent in Module 6
   queries the database you build in Module 2 and the RAG index from Module 5).
2. **Daily pattern per week:** 📖 read the theory doc (WHY first, with analogies) → 💻 work the
   notebook → ✏️ do exercises (collapsible solutions) → 🔨 advance the module project.
3. **Built to be remembered, not just understood.** Every theory doc opens with predict-first
   questions, marks each concept with a one-line "remember this", asks recall questions *before*
   giving answers, and ends with a spaced-review section that re-tests earlier days. Each module
   ships a cheat sheet. Every code construct is broken down token by token the first time it appears.
4. **Content is delivered weekly.** Only the modules marked 📗 are authored. When you finish a week,
   ask Claude Code for the next one — it reads [PLAN.md](PLAN.md) and authors the next week's
   materials. This keeps the course adaptive to your actual progress.
5. **Ship the projects.** Each `project-*/` folder is self-contained: copy it to its own public
   GitHub repo, get the CI badge green, deploy it. That's your portfolio.

---

## 🛠️ Prerequisites

- **Python 3.10+**, **VS Code** (with Jupyter extension), **Docker Desktop**, **Git** + a GitHub account
- From Module 3: a free **Azure** account (guide provided in `docs/`)
- From Module 4: an OpenAI or Anthropic API key — total course budget **€10–20**; a free local
  fallback via **Ollama** is used for all iterative development
- Basic programming knowledge; no data engineering or AI experience assumed

---

## 📁 Repo Layout

```
├── PLAN.md                          # Master plan + progress tracker (source of truth)
├── docs/                            # Shared guides (Docker, Git, Azure, LLM budget)
├── module-01-python-foundations/    # lessons/ + exercises/ + project-datacli/
├── module-02-sql-elt-pipeline/      # lessons/ + exercises/ + project-nl-open-data-pipeline/
├── module-03-fastapi-azure/         # ...
├── ...
└── module-07-capstone/
```

Each module: `README.md` (goals + schedule) · `lessons/` (theory + notebooks) · `exercises/` ·
`project-<name>/` (the portfolio artifact).

---

## 💡 Learning Philosophy

1. **Explain WHY before HOW** — every concept starts with the problem it solves
2. **Start from zero** — no assumptions, jargon explained on first use
3. **Hard way first** — e.g., build a raw agent loop before touching LangGraph
4. **Projects over toys** — every module produces something deployable and demo-able
5. **Production habits from day one** — types, tests, CI, logging, cost control

---

## 📞 Getting Help

- Each module README has setup + troubleshooting
- Docker issues → [docs/DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md)
- Exercises include collapsible solutions for when you're stuck

---

**Last updated:** 2026-09-08 · **Status:** Modules 1–2 done · **Module 3 ready** · Module 4 next

**Ready?** Continue with [Module 3: FastAPI, CI/CD & First Azure Deploy](module-03-fastapi-azure/README.md)
