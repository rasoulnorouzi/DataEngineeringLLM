# Module 7 — Capstone: `knowledge-copilot`

**Duration:** 3 weeks (~10 hrs/week) · **Status:** ⬜ planned — full spec authored when you get here (see [PLAN.md](../PLAN.md))

## The Project: "Ask HR" — Company Knowledge Copilot

A deployed internal assistant for a fictional Dutch company: employees ask questions in natural
language; the system answers from **company documents** (RAG over pgvector) *and* **live data**
(agent runs read-only SQL against the analytics DB), always with citations.

This is your flagship interview demo: **one URL, one public repo**, exercising every skill from the
course — FastAPI, RAG, agents, Docker, CI/CD, Azure, evals, tracing, cost control.

## Milestones

- **Week 1:** ingestion CLI + RAG core + FastAPI endpoints (composes Modules 3+5)
- **Week 2:** LangGraph agent routing (RAG tool vs SQL tool vs refuse/clarify), guardrails,
  minimal chat UI (static HTML or Streamlit)
- **Week 3:** hardening — pytest + eval suite in CI, Langfuse (free tier) tracing, cost caps,
  GitHub Actions CD to Azure Container Apps, README with architecture diagram + demo GIF

## Scope Guardrails (realism)

Single tenant · API-key auth only · ~30–50 seed documents (provided) · batch ingestion ·
streaming responses = stretch goal · gpt-4o-mini/Haiku with Ollama dev mode ·
everything runs locally with one `docker compose up`. Estimated API spend: **~€6**.

> *CV bullet:* "Shipped an end-to-end AI knowledge assistant (RAG + agents + FastAPI) to Azure with
> CI/CD, tracing, evals, and LLM cost guardrails."
