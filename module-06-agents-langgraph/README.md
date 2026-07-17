# Module 6 — Agents & Tool Harnessing

**Duration:** 2 weeks (~10 hrs/week) · **Status:** ⬜ planned — content authored when you get here (see [PLAN.md](../PLAN.md))

## Learning Goals

- What an agent loop *actually is* — build one **from scratch** with raw tool-calling first
  (model → tool call → result → model → …), so frameworks never feel like magic
- Then **LangGraph**: state, nodes, edges, conditional routing, retries, human-in-the-loop, memory
- Tool design: schemas, error handling, sandboxing (e.g., read-only SQL), guardrails
- Tracing and debugging agent runs

## Portfolio Project: `data-analyst-agent`

An agent that answers natural-language questions about the Module 2 database.
Tools: `run_sql` (read-only, sandboxed), `search_docs` (your Module 5 RAG), `plot_chart`.
LangGraph graph with a review/retry loop; conversation exposed via a FastAPI endpoint.
Estimated API spend: **~€5**.

> *CV bullet:* "Engineered a multi-tool LLM agent with LangGraph (SQL querying, document retrieval,
> self-correction loops) exposed via a FastAPI service."

## Prerequisites

- Modules 2, 4, 5 — this module is deliberately almost pure **composition** of what you built
