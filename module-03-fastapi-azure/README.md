# Module 3 — FastAPI, CI/CD & First Azure Deploy

**Duration:** 2 weeks (~10 hrs/week) · **Status:** ⬜ planned — content authored when you get here (see [PLAN.md](../PLAN.md))

## Learning Goals

- HTTP & REST from zero: methods, status codes, JSON APIs
- FastAPI: path/query params, Pydantic request/response models, dependency injection, async basics
- Testing APIs with `TestClient` / httpx
- Production Dockerfile for a Python service (multi-stage, non-root)
- CI/CD with GitHub Actions: test → build image → push → **deploy to Azure Container Apps** on merge
- Secrets & configuration management (env vars, GitHub secrets, Azure)

## Portfolio Project: `insight-api`

A containerized FastAPI service exposing analytics from your Module 2 database
(e.g., `/stations/{id}/weather-summary`, `/trends`), auto-deployed to Azure Container Apps with
live OpenAPI docs at a public URL.

> *CV bullet:* "Developed and deployed a containerized FastAPI analytics service to Azure Container
> Apps with a full CI/CD pipeline (test, build, deploy on merge)."

## Prerequisites

- Module 2 completed (its database + Docker skills are the foundation)
- Free Azure account — setup guide will be authored with this module (`docs/AZURE_SETUP_GUIDE.md`)
