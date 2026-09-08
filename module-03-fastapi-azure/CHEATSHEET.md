# Module 3 Cheat Sheet — FastAPI to Azure

Everything from Days 1–8 on a few screens. Keep it open while you build the project.
Each section names the day it came from, so you know where to go back to.

---

## Day 1 — HTTP

```
REQUEST                            RESPONSE
  method   GET                       status   200
  path     /weather/daily            headers  Content-Type: application/json
  query    ?city=Amsterdam           body     {"city": "Amsterdam", ...}
  headers  Accept: application/json
  body     (POST/PUT/PATCH only)
```

| Method | Meaning | Safe? | Idempotent? |
|---|---|---|---|
| `GET` | read | ✅ | ✅ |
| `POST` | create | ❌ | ❌ |
| `PUT` | replace | ❌ | ✅ |
| `PATCH` | partial edit | ❌ | usually ❌ |
| `DELETE` | remove | ❌ | ✅ |

**Safe** = changes nothing. **Idempotent** = twice equals once (Module 2's light switch).

| Code | Use it when |
|---|---|
| `200` | success with a body |
| `201` | a POST created something |
| `204` | success, deliberately nothing to return |
| `400` | malformed request |
| `401` | **who are you?** (unauthenticated) |
| `403` | I know who you are, and no |
| `404` | no such resource |
| `422` | shape fine, **values** invalid — FastAPI's default |
| `429` | rate limited |
| `500` | **my** unhandled exception |
| `503` | **my dependency** is down |

> **`4xx` = your fault. `5xx` = my fault.** Getting `500` vs `503` right decides who gets paged.

**REST:** nouns in the path, verbs in the method.
`/cities` collection · `/cities/Utrecht` item · **path = which thing, query = how you want it.**

**JSON:** 6 types · double quotes only · no trailing comma · no comments · **no dates, no `Decimal`**.

---

## Day 2 — FastAPI

```python
from fastapi import FastAPI, Query, HTTPException, status
app = FastAPI()                                  # the registry

@app.get("/cities/{name}")                       # writes a row in the routing table
def read_city(                                   # "path operation function"
    name: str,                                   # in the path      -> PATH param
    limit: int = Query(10, ge=1, le=100),        # not in the path  -> QUERY param
):
    if unknown:
        raise HTTPException(404, detail=f"City {name!r} not found")   # RAISE, don't return
    return {"city": name}                        # dict -> JSON automatically
```

```bash
uvicorn main:app --reload        # module : variable-inside-it
#       ^^^^ ^^^
```

| | |
|---|---|
| The type hint | is the **doorman**: converts, validates, documents |
| A default value | makes a parameter optional |
| **Specific routes first** | `/users/me` **above** `/users/{id}`, or `me` is swallowed |
| `/docs` `/redoc` `/openapi.json` | free, and cannot drift out of date |
| `--host 0.0.0.0` | required inside a container (Day 7) |

**Import time registers. Request time executes.**

---

## Day 3 — Pydantic v2

```python
class CityIn(BaseModel):                          # THE ORDER FORM (in)
    name: str = Field(min_length=1, max_length=100)
    lat: float = Field(ge=-90, le=90)
    country: str = "NL"                           # default => optional

    @field_validator("name")
    @classmethod
    def clean(cls, v): return v.strip().title()   # return value REPLACES the field

class CityOut(CityIn):                            # THE PLATING STANDARD (out)
    model_config = ConfigDict(from_attributes=True)   # read ORM rows, not just dicts
    id: int                                       # server-assigned; caller can't supply it

@app.post("/cities", response_model=CityOut, status_code=201)
def create(city: CityIn): ...                     # model in signature => request BODY
```

| Spelling | Key may be missing? | Value may be null? |
|---|---|---|
| `a: int` | ❌ | ❌ |
| `b: int = 0` | ✅ | ❌ |
| `c: int \| None` | ❌ | ✅ |
| `d: int \| None = None` | ✅ | ✅ |

**The type controls allowed values. The default controls whether the key may be missing.**

**`response_model` does four jobs:** filters (allow-list — undeclared fields *cannot* leak) ·
converts (`Decimal`→number, `date`→string) · validates your own output · documents.

**Errors:** `422`, a **list**, each `{type, loc, msg, input}`. `loc` reads outside in:
`["body", "cities", 2, "location", "lat"]`.

> **v2, not v1:** `model_dump()` `model_validate()` `ConfigDict`. Not `.dict()` `.parse_obj()`.

---

## Day 4 — Dependencies & the database

```python
# CONFIG — environment > .env > default
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg2://..."

@lru_cache
def get_settings(): return Settings()

# ENGINE — once per APPLICATION
@asynccontextmanager
async def lifespan(app):
    app.state.engine = create_engine(url, pool_pre_ping=True)
    yield
    app.state.engine.dispose()

# CONNECTION — once per REQUEST
def get_conn(request: Request):
    with request.app.state.engine.connect() as conn:
        yield conn                    # setup / handler / teardown

@app.get("/weather/daily")
def read(city: str, conn = Depends(get_conn)):        # Depends(f) NOT Depends(f())
    return conn.execute(
        text("SELECT ... WHERE city = :city"),        # BIND every value
        {"city": city},
    ).mappings().all()
```

| | |
|---|---|
| Dependency injection | **ask, don't build** |
| `Depends(f)` vs `Depends(f())` | recipe vs meal. Always the recipe |
| `yield` + `finally` | teardown guaranteed, even when the handler raises |
| `engine.begin()` vs `.connect()` | commits vs doesn't. DDL/DML need `begin()` |

**🚨 SQL safety**

```python
# values -> bind parameters, always
text("... WHERE city = :city"), {"city": city}

# identifiers CANNOT be bound -> allow-list
SORTABLE = {"date": "obs_date", "temp": "temp_max_c"}
column = SORTABLE.get(sort_by) or raise HTTPException(422, ...)
```

The caller supplies a **key**; you supply the column.

**Health:** `/health` = liveness, no dependencies → *restart me*.
`/health/ready` = readiness, checks the database, **503** → *stop routing to me*.

---

## Day 5 — Testing

```python
client = TestClient(app)              # no server, no port, no network

app.dependency_overrides[get_conn] = fake_conn      # THE SWAP
...
app.dependency_overrides.clear()                    # in a fixture's teardown
```

**Assert five things per endpoint:**

1. status code · 2. shape · 3. key values · 4. **a failure case** · 5. **nothing leaks**

```python
assert set(body) == {"id", "email"}     # exact equality ONLY when the key set IS the contract
```

| | |
|---|---|
| `json=` vs `data=` | JSON body vs form encoding. You want `json=` |
| unit vs integration | contracts vs **SQL** |
| `12 passed, 4 skipped` | **is not** `16 passed` |

```bash
pytest -v · pytest f.py::test_x · pytest -k word · pytest -x · pytest --lf · pytest -rs
```

---

## Day 6 — Async

| You write | Runs on | Blocking code inside is |
|---|---|---|
| `def` | a **threadpool** | ✅ safe |
| `async def` | the **event loop** | 🚨 freezes **every** request |

> **If you're not `await`ing anything, use plain `def`.**

`async def` defines · `await` pauses · `asyncio.gather` runs many at once ·
a coroutine you forgot to `await` does **nothing**.

Async helps **I/O-bound** work (waiting). It does nothing for **CPU-bound** work.
`insight-api` uses `def` handlers because psycopg2 blocks — correct, not lazy.

**Every outbound call gets a timeout.**
`(pool_size + max_overflow) × workers × containers < max_connections (100)`

---

## Day 7 — Docker

```dockerfile
FROM python:3.12-slim AS builder     # pin it. slim, not alpine (musl breaks wheels)
WORKDIR /app
COPY pyproject.toml ./               # LEAST-changing first
RUN pip install --no-cache-dir --prefix=/install .
COPY src/ ./src/                     # MOST-changing last

FROM python:3.12-slim                # fresh slate: compilers don't ship
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /install /usr/local
COPY --from=builder /app/src ./src
USER appuser                         # after installs, before CMD
EXPOSE 8000                          # DOCUMENTATION ONLY
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]   # exec form
```

| Trap | Fix |
|---|---|
| Slow rebuilds | dependencies before source (one cache miss kills every layer below) |
| Empty reply from container | `--host 0.0.0.0` |
| Port unreachable | `-p 8000:8000`; `EXPOSE` publishes nothing |
| Can't reach host database | `host.docker.internal`, not `localhost` |
| Secrets in the image | `.dockerignore` with `.env` — `rm` in a later layer does **not** unpublish |
| Killed mid-request | exec-form `CMD`, or `sh` swallows `SIGTERM` |
| "Which version is live?" | tag with the **commit SHA** |
| `COPY . .   # comment` fails | `#` only starts a comment at the **start of a line** |

---

## Day 8 — Azure & CD

```
Resource Group > [ ACR (the depot) ] + [ Environment > Container App ]
az group delete --name $RG --yes --no-wait        # removes ALL of it
```

```bash
az acr build --registry $ACR --image app:$SHA .            # builds IN THE CLOUD
az containerapp update --name app --resource-group $RG \
  --image $ACR.azurecr.io/app:$SHA                         # NEW TAG EVERY TIME
az containerapp secret set --name app -g $RG --secrets db-url="..."   # name ≤ 20 chars
az containerapp update --name app -g $RG --set-env-vars DATABASE_URL=secretref:db-url
```

**💸 Cost**

| | |
|---|---|
| Container Apps free/month | 180,000 vCPU-s · 360,000 GiB-s · 2M requests |
| `--min-replicas 0` | idle costs **nothing** (cold start is the trade) |
| **ACR Basic** | **~€5/month, NO free tier**, bills while asleep |
| Free account | **$200 credit, 30 days** |

**🎫 OIDC — a visitor badge, not a copied key**

```yaml
permissions:
  id-token: write        # MANDATORY, or login fails
  contents: read

- uses: azure/login@v3   # v1 is EOL; Microsoft's own docs still show v1
```

```bash
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters credential.json
#                                          ^^^ OBJECT id, NOT the client/app id
```

```
subject, repos created AFTER 15 Jul 2026:
  repo:owner@<ownerId>/repo@<repoId>:ref:refs/heads/main
```

> 🚨 **A wrong `subject` is created without error and fails silently later.** If login fails,
> suspect this first. No wildcards. Max 20 credentials per app.

**Safety:** `cd.yml` has `needs: test` — a red build can never deploy.
**Rollback** = activate the previous revision.

---

## The metaphors, in order

| Thing | Metaphor |
|---|---|
| API | a restaurant with a written menu |
| Endpoint | a dish on the menu |
| Status code | the waiter's answer |
| Pydantic request model | the order form checked at the door |
| `response_model` | the plating standard — what may leave the pass |
| Dependency injection | the shared prep station (the waiter doesn't grow vegetables) |
| Async | one waiter, many tables |
| Container image | a **food truck** |
| Registry | the **depot** |
| Azure Container Apps | the **festival ground** that rents you a pitch |
| CI | the bouncer *(Module 2)* |
| Scheduled run | the night shift *(Module 2)* |
| CD | the delivery driver |
| OIDC | a visitor badge that expires, not a copied key |
