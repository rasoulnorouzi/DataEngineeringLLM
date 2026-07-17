# Module 4 — LLM Engineering Fundamentals

**Duration:** 2 weeks (~10 hrs/week) · **Status:** ⬜ planned — content authored when you get here (see [PLAN.md](../PLAN.md))

## Learning Goals

- How LLMs actually work: tokens, context windows, temperature, why they hallucinate
- Calling OpenAI/Anthropic APIs properly; **structured outputs** (JSON mode → Pydantic validation)
- Tool / function calling — the primitive behind all agents
- Prompt engineering as *engineering*: versioned prompts, regression-tested
- **Evals with pytest**: golden sets, LLM-as-judge basics, running evals in CI
- Cost control: token budgets, cheap-model-first, and a provider-abstraction layer with a free
  local **Ollama** fallback

## Portfolio Project: `doc-extract`

An LLM-powered document extraction service: feed it invoices/CVs/emails, get validated structured
JSON out. Includes an eval suite (accuracy on ~20 golden documents) that runs in CI.
Estimated API spend: **~€3** (gpt-4o-mini / Claude Haiku; Ollama for dev).

> *CV bullet:* "Built an LLM-powered document extraction service with structured outputs, an
> automated evaluation suite in CI, and multi-provider fallback (OpenAI/Ollama) for cost control."

## Prerequisites

- Modules 1–3 (Pydantic validation, FastAPI/Docker/CI scaffold)
- An OpenAI or Anthropic API key — budget guide authored with this module (`docs/LLM_BUDGET_GUIDE.md`)
