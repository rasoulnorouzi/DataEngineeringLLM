# Module 3 — FastAPI, CI/CD & First Azure Deploy

**Duration:** 2 weeks (~10 hrs/week) · **Status:** 📗 fully authored

By the end of this module you can build an HTTP API over a real database, test it without a database,
put it in a container, and deploy it to Azure automatically on every merge — your first **live,
public URL** to put on a CV.

> **Lost? Follow the route below top-to-bottom. Every step names the exact file to open.
> Never skip a ☑ box.**

---

## 🧭 Your Route Through This Module

### Step 0 — Setup (~20 min, do once)

- [ ] Create the module environment:

```bash
cd module-03-fastapi-azure
python -m venv .venv
.venv\Scripts\activate              # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

- [ ] Start the Module 2 database (Days 4, 9 and 10 need it):

```bash
cd ../module-02-sql-elt-pipeline/project-nl-open-data-pipeline
docker compose -f docker/docker-compose.yml up -d
docker ps        # expect week2_postgres (healthy)
```

- [ ] Confirm the warehouse has data. If this returns nothing, run `python -m pipeline.run` first:

```bash
docker exec week2_postgres psql -U student -d week2_db -c "SELECT count(*) FROM staging.weather_clean;"
```

**Checkpoint:** `python -c "import fastapi; print(fastapi.__version__)"` prints a version, and the
query above returns a row count above zero → you're ready for Day 1.

---

### Week A — Build the API (Days 1–5, ~2–2.5 h each)

Same rhythm every day: **read theory → run notebook → do exercise**.

- [ ] **Day 1 (~2h)** — HTTP & REST from zero
      1. Read [lessons/day1-http-and-rest/01_theory_http_and_rest.md](lessons/day1-http-and-rest/01_theory_http_and_rest.md)
      2. Notebook [lessons/day1-http-and-rest/02_http_practice.ipynb](lessons/day1-http-and-rest/02_http_practice.ipynb)
         — send real requests, trigger a 404 and a 422, watch POST duplicate an order twice
      3. Exercise [exercises/exercise_1_http_and_rest.ipynb](exercises/exercise_1_http_and_rest.ipynb)

- [ ] **Day 2 (~2.5h)** — your first FastAPI app
      1. Read [lessons/day2-fastapi-basics/03_theory_fastapi_fundamentals.md](lessons/day2-fastapi-basics/03_theory_fastapi_fundamentals.md)
      2. Notebook [lessons/day2-fastapi-basics/04_fastapi_practice.ipynb](lessons/day2-fastapi-basics/04_fastapi_practice.ipynb)
         — includes the route-order bug, reproduced on purpose
      3. Exercise [exercises/exercise_2_fastapi_endpoints.ipynb](exercises/exercise_2_fastapi_endpoints.ipynb)

- [ ] **Day 3 (~2.5h)** — Pydantic: order forms and plating standards
      1. Read [lessons/day3-pydantic-validation/05_theory_pydantic_models.md](lessons/day3-pydantic-validation/05_theory_pydantic_models.md)
      2. Notebook [lessons/day3-pydantic-validation/06_pydantic_practice.ipynb](lessons/day3-pydantic-validation/06_pydantic_practice.ipynb)
         — watch a `response_model` refuse to leak a password hash
      3. Exercise [exercises/exercise_3_pydantic_validation.ipynb](exercises/exercise_3_pydantic_validation.ipynb)

- [ ] **Day 4 (~2.5h)** — dependency injection & talking to Postgres *(needs the database up)*
      1. Read [lessons/day4-dependencies-and-db/07_theory_dependency_injection.md](lessons/day4-dependencies-and-db/07_theory_dependency_injection.md)
      2. Notebook [lessons/day4-dependencies-and-db/08_db_and_deps_practice.ipynb](lessons/day4-dependencies-and-db/08_db_and_deps_practice.ipynb)
         — you perform a real SQL injection on a throwaway table, then defeat it

- [ ] **Day 5 (~2.5h)** — testing an API without a server or a database
      1. Read [lessons/day5-testing-apis/09_theory_testing_apis.md](lessons/day5-testing-apis/09_theory_testing_apis.md)
      2. Notebook [lessons/day5-testing-apis/10_api_testing_practice.ipynb](lessons/day5-testing-apis/10_api_testing_practice.ipynb)
         — real pytest runs, real failure messages, red → green
      3. Exercise [exercises/exercise_4_testing_apis.ipynb](exercises/exercise_4_testing_apis.ipynb)

**Checkpoint:** you can say, in one sentence each: where a parameter comes from, what `response_model`
does, why `Depends` makes testing easy, and what `12 passed, 4 skipped` proves about your SQL.

---

### Week B — Ship it (Days 6–10)

- [ ] **Day 6 (~2h)** — async, and the mistake that freezes a service
      1. Read [lessons/day6-async/11_theory_async_basics.md](lessons/day6-async/11_theory_async_basics.md)
      2. Notebook [lessons/day6-async/12_async_practice.ipynb](lessons/day6-async/12_async_practice.ipynb)
         — starts a real uvicorn server and measures one request blocking every other one

- [ ] **Day 7 (~2.5h)** — the food truck: containerising your API *(needs Docker running)*
      1. Read [lessons/day7-docker-for-apps/13_theory_production_dockerfile.md](lessons/day7-docker-for-apps/13_theory_production_dockerfile.md)
      2. Notebook [lessons/day7-docker-for-apps/14_docker_practice.ipynb](lessons/day7-docker-for-apps/14_docker_practice.ipynb)
         — measures the cache-order difference and reproduces the `127.0.0.1` bug
      3. New to Docker? [docs/DOCKER_GUIDE.md](../docs/DOCKER_GUIDE.md) covers the basics from Module 2

- [ ] **Day 8 (~3h)** — Azure Container Apps and continuous deployment
      1. Read [lessons/day8-azure-and-cd/15_theory_azure_container_apps.md](lessons/day8-azure-and-cd/15_theory_azure_container_apps.md)
      2. **Work through [docs/AZURE_SETUP_GUIDE.md](../docs/AZURE_SETUP_GUIDE.md)** — account,
         **budget alert first**, CLI, and the OIDC federated credential
      3. Notebook [lessons/day8-azure-and-cd/16_cd_pipeline_practice.ipynb](lessons/day8-azure-and-cd/16_cd_pipeline_practice.ipynb)
         — generates your exact credential `subject` and audits your workflow before it fails

- [ ] **Days 9–10 (~3h)** — THE PROJECT
      1. Open [project-insight-api/PROJECT_GUIDE.md](project-insight-api/PROJECT_GUIDE.md) and work
         through Parts 1→5, then its six milestones
      2. Publish, deploy, then **tear down** so the meter stops

---

## 💸 Read this before Day 8

This is the only module with a real (small) cost.

| | Cost |
|---|---|
| Azure Container Apps at demo scale, scaled to zero | **free** — 180,000 vCPU-seconds and 2M requests free per month |
| **Azure Container Registry (Basic)** | **~€5/month, no free tier**, bills even while your app sleeps |
| New Azure account credit | **$200, usable within 30 days** |

Set a **budget alert before creating anything** — the setup guide does this before it does anything
else — and run `az group delete` when you're finished. Rebuilding from your repo takes ten minutes,
and being able to say that is a better interview answer than "it's still running".

---

## 🏆 Portfolio Project: `insight-api`

A containerized FastAPI service over the Module 2 warehouse, deployed to Azure Container Apps with
CI/CD, OIDC (no stored secrets), and live OpenAPI docs.

Two documents, two purposes:
- [PROJECT_GUIDE.md](project-insight-api/PROJECT_GUIDE.md) — **for you**: full walkthrough, code
  explained file by file, design rationale, a transferable recipe, and the milestones
- [README.md](project-insight-api/README.md) — **for recruiters**: what ships when you publish it

> *CV bullet:* "Developed and deployed a containerized FastAPI analytics service to Azure Container
> Apps with a full CI/CD pipeline (test, build, deploy on merge)."

---

## 🧠 Recall aids

- **[CHEATSHEET.md](CHEATSHEET.md)** — the whole module on a few screens. Print it, or keep it open
  while you work on the project.
- Every theory doc opens with **predict-first questions** and closes with a **spaced review** section
  that re-tests earlier days. Do them without scrolling — retrieving is what makes it stick.
- The running metaphor: an API is a **restaurant** (menu, orders, kitchen), a container image is a
  **food truck**, the registry is the **depot**, Azure is the **festival ground**, CD is the
  **delivery driver**, and OIDC is a **visitor badge** instead of a copied key.

---

## ✅ Definition of Done

- [ ] Every checkbox above ticked
- [ ] `uvicorn insight_api.main:app --reload` serves `/docs` against your Module 2 data
- [ ] `pytest -v` green **with integration tests running, not skipping**; `ruff check .` clean
- [ ] You added your own endpoint and tests (Project Milestones 3 and 4)
- [ ] `docker build` works; the container runs as a non-root user
- [ ] Project published as your own public repo, **CI badge green**
- [ ] Deployed to Azure, live URL in the README, then **torn down**
- [ ] You can explain out loud: why the handlers are `def`, why values are bound and identifiers
      allow-listed, and what `needs: test` prevents

Then report **"Module 3 done"** so [PLAN.md](../PLAN.md) gets updated — and ask for **Module 4**.
