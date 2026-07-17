# Module 5 — RAG & Vector Databases

**Duration:** 2 weeks (~10 hrs/week) · **Status:** ⬜ planned — content authored when you get here (see [PLAN.md](../PLAN.md))

## Learning Goals

- Embeddings intuition: what "meaning as a vector" means, similarity, when it fails
- Chunking strategies and why they dominate RAG quality
- **pgvector** — vector search inside the PostgreSQL you already know from Module 2
- Similarity search, hybrid search (vectors + keywords), metadata filtering
- **Retrieval evaluation**: recall@k, faithfulness, building a small eval set
- Grounded answers with source citations; common RAG failure modes

## Portfolio Project: `ask-my-docs`

A RAG API: batch-ingest a folder of PDFs/Markdown into pgvector; a `/ask` endpoint returns grounded
answers **with source citations**; a retrieval-quality eval report is committed to the repo.
Deployed to Azure. Estimated API spend: **~€4** (embeddings are cheap; Ollama fallback available).

> *CV bullet:* "Implemented a production-style RAG system with pgvector, chunking and hybrid
> retrieval, source-cited answers, and measured retrieval quality (recall@k)."

## Prerequisites

- Modules 2–4 (Postgres/Docker, FastAPI deploys, LLM API + provider abstraction)
