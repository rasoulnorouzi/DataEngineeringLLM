# Day 2 — FastAPI Fundamentals: Your First Menu

**Time:** ~2.5 h · **Prerequisite:** Day 1 (methods, paths, status codes)

Yesterday you learned to *order* at the counter. Today you build the counter.

---

## 🧠 Before you read — predict first

1. To make a URL like `/cities/Utrecht` work, how do you think the framework knows that `Utrecht`
   is data and not part of the address?
2. Python has type hints (`def f(x: int)`). Normally they do nothing at runtime. What could a web
   framework do with them?
3. Every API needs documentation, and documentation always drifts out of date. How might a framework
   make that impossible?

---

## 1. What FastAPI is, and the one idea behind it

FastAPI is a Python library for building HTTP APIs. Its distinguishing idea is small and radical:

> **Your type hints are the specification.**

In most frameworks you write the code, then *separately* write validation, *separately* write
documentation, and then maintain three things that slowly disagree with each other. FastAPI reads
your function signature and derives all three.

Compare. This is Flask, the older standard:

```python
@app.route("/items/<item_id>")
def read_item(item_id):
    item_id = int(item_id)          # you convert
    if item_id < 1:                 # you validate
        return {"error": "bad id"}, 400   # you handle the error
    return {"item_id": item_id}
    # and you write the docs somewhere else, by hand, forever
```

This is FastAPI:

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

The `: int` did all four jobs. It converts `"7"` to `7`, rejects `"abc"` with a `422` and a message
naming the field, and publishes a machine-readable schema saying this endpoint takes an integer.

> 🎯 **Remember this** — in FastAPI the type hint is the **doorman**. It checks ID at the door, so
> your function body only ever sees guests who are already valid.

That doorman image is worth holding on to. Almost everything surprising about FastAPI is the doorman
doing his job before your code runs.

---

## 2. The smallest possible app, token by token

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "hello"}
```

Five lines, and beginners get stuck on four of them. So:

### `from fastapi import FastAPI`

Lowercase `fastapi` is the **package** (the installed library). Uppercase `FastAPI` is the **class**
inside it. Python convention: modules lowercase, classes CapitalCase. They are not the same word
doing double duty; they're two different things that happen to be spelled similarly.

### `app = FastAPI()`

You are **instantiating** the class — calling it with `()` builds one object. That object *is* your
application: the registry that will hold every route you define. The name `app` is a convention, not
a requirement, but keep it, because the command that runs your server has to be told this name and
every tutorial assumes `app`.

### `@app.get("/")`

This is a **decorator**, and it is the piece that confuses everyone, so let's take it apart properly.

A decorator is a function that takes your function and does something with it. The `@` syntax is
pure sugar:

```python
@app.get("/")
def read_root():
    ...

# means exactly this:
def read_root():
    ...
read_root = app.get("/")(read_root)
```

Read the desugared line right to left: `app.get("/")` returns a *decorator*, that decorator is
called with your function, and FastAPI's version does one thing — **it writes your function into the
app's routing table under the key (GET, "/")** — and hands the function back unchanged.

So the mental model is a **register**:

| The decorator | Says |
|---|---|
| `@app.get("/")` | "When a GET arrives for `/`, call this function" |
| `@app.post("/cities")` | "When a POST arrives for `/cities`, call this function" |
| `@app.delete("/cities/{name}")` | "When a DELETE arrives for `/cities/<anything>`, call this" |

The method in the decorator name (`get`, `post`, `put`, `patch`, `delete`) is the HTTP method from
Day 1. The string is the path. That's the entire API of routing.

The decorated function has a name of its own: the **path operation function**, or informally the
**handler** or **view function**. Its name (`read_root`) is never visible to callers — only the path
is. Name it for the human reading the code.

### `return {"message": "hello"}`

You return a **Python dict**. FastAPI serialises it to JSON and sets `Content-Type: application/json`
for you. You never call `json.dumps` and you never build a response object by hand for the ordinary
case.

> 🎯 **Remember this** — `app` is the registry, `@app.get(path)` writes a row into it, and returning
> a dict is enough.

### 🔁 Recall check

<details>
<summary>Without scrolling: what does <code>@app.get("/health")</code> above <code>def check():</code> actually <em>do</em> at import time?</summary>

At the moment Python imports the module, it calls `app.get("/health")`, gets back a decorator, calls
that decorator with `check`, and FastAPI records "(GET, /health) → check" in the app's routing table.
The function itself is unchanged and is **not** called. It will be called later, once per matching
request.

Import time registers; request time executes. Keep those two clocks separate in your head and
FastAPI stops surprising you.
</details>

---

## 3. Running it: uvicorn, token by token

Your file is `main.py`, containing `app`. To serve it:

```bash
uvicorn main:app --reload
```

| Token | Meaning |
|---|---|
| `uvicorn` | The **server** programme. FastAPI writes responses; uvicorn is what actually speaks HTTP on a socket |
| `main` | The **module** — the file `main.py`, without the `.py` |
| `:` | Separator between module and the object inside it |
| `app` | The **variable** inside that module. This is why the name matters |
| `--reload` | Watch the files and restart on save. **Development only** |

Common variations:

```bash
uvicorn main:app --reload --port 8001        # different port (default 8000)
uvicorn main:app --host 0.0.0.0 --port 8000  # listen on all interfaces - needed in Docker (Day 7)
uvicorn src.insight_api.main:app             # dotted path into a package
```

`--host 0.0.0.0` will matter enormously on Day 7. The default host is `127.0.0.1`, which means "only
accept connections from this machine". Inside a container, "this machine" is the container, so a
container serving on `127.0.0.1` is unreachable from outside and you get a confusing empty reply.
`0.0.0.0` means "accept on every network interface". Note it now; you'll meet the bug later.

**Why is FastAPI not a server?** Because that separation lets you swap servers. FastAPI speaks a
Python-level protocol called **ASGI** (Asynchronous Server Gateway Interface) — a contract for "how a
Python web app and a Python web server talk". Uvicorn is one ASGI server; there are others. Your app
doesn't care.

Once it's running, open:

| URL | What it is |
|---|---|
| `http://127.0.0.1:8000/` | Your endpoint |
| `http://127.0.0.1:8000/docs` | **Swagger UI** — interactive docs you can click "Try it out" in |
| `http://127.0.0.1:8000/redoc` | ReDoc — the same information, prettier for reading |
| `http://127.0.0.1:8000/openapi.json` | The raw machine-readable schema everything else is built from |

Nobody wrote those docs. FastAPI generated them from your function signatures. This is the answer to
prediction question 3: docs can't drift out of date if they are *derived from* the code rather than
maintained beside it.

> 🎯 **Remember this** — `uvicorn main:app` = "in file `main`, serve the object `app`". `/docs` is
> free and always accurate.

---

## 4. Path parameters: which thing

Day 1: **path = which thing**. In FastAPI, a path segment in `{braces}` becomes a function argument
with the same name.

```python
@app.get("/cities/{city_name}")
def read_city(city_name: str):
    return {"city": city_name}
```

`GET /cities/Utrecht` → `{"city": "Utrecht"}`.

Two rules, and both are enforced:

1. **The name in the braces must match the parameter name exactly.** `{city_name}` needs
   `city_name`. A mismatch is an error at import time, not a silent 404 — FastAPI checks at startup.
2. **The type hint is applied to the value.**

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "type": str(type(item_id))}
```

| Request | Result |
|---|---|
| `GET /items/7` | `200` → `{"item_id": 7, ...}` — note **7**, not `"7"` |
| `GET /items/abc` | `422` → a JSON error naming the field and the problem |

URLs are text. Everything arrives as a string. `: int` is what turns `"7"` into `7`, and it's why
you can do arithmetic on `item_id` in the body of the function without thinking about it. FastAPI
calls this **parsing**; the wider name for a type hint that has a runtime effect is **coercion**.

The `422` body is worth reading once, because you'll see it a thousand times:

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "item_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
    }
  ]
}
```

`loc` is the **location** — a path from the outside in: "in the path, the field `item_id`". When you
nest models on Day 3 this becomes `["body", "location", "lat"]` and it will save you a lot of time.

### ⚠️ Route order matters

```python
@app.get("/users/{user_id}")
def read_user(user_id: int): ...

@app.get("/users/me")           # ❌ unreachable
def read_me(): ...
```

FastAPI matches **in definition order, first match wins**. `/users/me` arrives, is tested against
`/users/{user_id}` first, matches (`me` is *something*), and then `: int` rejects it with a `422`.
Your `me` handler is never reached.

Fix: **specific routes before generic ones.**

```python
@app.get("/users/me")          # ✅ specific first
def read_me(): ...

@app.get("/users/{user_id}")   # ✅ generic second
def read_user(user_id: int): ...
```

> 🎯 **Remember this** — `{braces}` in the path become arguments; the type hint is the doorman; and
> **specific routes go above generic ones**, always.

### 🔁 Recall check

<details>
<summary>You define <code>/weather/{city}</code> and then <code>/weather/summary</code>. A request for <code>/weather/summary</code> returns 200 with <code>{"city": "summary"}</code>. Explain, and fix it.</summary>

`/weather/{city}` was defined first and matched. Because `city` is typed `str`, the literal text
`summary` is a perfectly valid city name as far as the doorman is concerned, so it passed and your
summary handler was never consulted. (Had `city` been `int`, you'd have got a `422` instead — same
bug, louder symptom.)

Fix: move `@app.get("/weather/summary")` **above** the parameterised route. This is the single most
common routing bug in every framework that does first-match routing.
</details>

---

## 5. Query parameters: how you want it

Day 1: **query = how you want it**. In FastAPI the rule is beautifully simple:

> A function parameter whose name is **not** in the path is a **query parameter**.

```python
@app.get("/weather/daily")
def read_daily(city: str, limit: int = 10, order: str = "asc"):
    return {"city": city, "limit": limit, "order": order}
```

`GET /weather/daily?city=Utrecht&limit=3` → `{"city": "Utrecht", "limit": 3, "order": "asc"}`

**Required vs optional is decided by the default value**, exactly as in ordinary Python:

| Signature | Behaviour |
|---|---|
| `city: str` | **Required.** Missing → `422` |
| `limit: int = 10` | **Optional**, defaults to 10 |
| `order: str \| None = None` | **Optional**, defaults to `None` — "the caller said nothing" |

That third form matters when "absent" and "empty" mean different things. `order: str = ""` can't
distinguish "caller omitted it" from "caller sent an empty string"; `str | None = None` can.

`str | None` is modern Python union syntax (3.10+) and reads as "a string **or** None". You may see
the older `Optional[str]` from `typing` in other codebases; they mean the same thing.

Booleans get friendly treatment:

```python
@app.get("/cities")
def list_cities(active_only: bool = False): ...
```

`?active_only=true`, `?active_only=True`, `?active_only=1`, `?active_only=yes`, and `?active_only=on`
all arrive as `True`. `false/False/0/no/off` arrive as `False`. Anything else is a `422`.

### Adding constraints and documentation with `Query`

The plain default gets you far, but you often want limits. That's `Query`:

```python
from fastapi import Query

@app.get("/weather/daily")
def read_daily(
    city: str,
    limit: int = Query(default=10, ge=1, le=100, description="Rows to return"),
):
    ...
```

| Token | Meaning |
|---|---|
| `Query(...)` | "This is a query parameter, and here are extra rules" |
| `default=10` | The value when the caller omits it |
| `ge=1` | **g**reater than or **e**qual to 1 |
| `le=100` | **l**ess than or **e**qual to 100 |
| `description=` | Text that appears in `/docs` |

Also available: `gt` / `lt` (strictly greater/less), `min_length` / `max_length` for strings, and
`pattern=` for a regular expression. Violate any of them and the caller gets a `422` naming the
constraint — you never write the check.

`Query(default=...)` with an ellipsis, `Query(...)`, is an old idiom meaning "required, but I still
want constraints". You'll see it in older code; `Query()` with no default now means the same thing.

> 🎯 **Remember this** — **in the path → path parameter; not in the path → query parameter.**
> A default value makes it optional. `Query()` adds rules and docs.

### 🔁 Recall check

<details>
<summary>Write a signature for <code>GET /weather/daily</code> that requires <code>city</code>, accepts an optional <code>from_date</code>, and takes a page size between 1 and 500 defaulting to 50.</summary>

```python
from datetime import date
from fastapi import Query

@app.get("/weather/daily")
def read_daily(
    city: str,
    from_date: date | None = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    ...
```

Note `date` as a type: FastAPI parses `?from_date=2026-09-01` into a real `datetime.date` object, and
returns a `422` for `?from_date=not-a-date`. You did not write a parser. This works for `date`,
`datetime`, `time`, `UUID`, `Decimal`, and `Enum` too.
</details>

---

## 6. Controlling the response

### Status codes

The default is `200`. Change it in the decorator:

```python
from fastapi import status

@app.post("/cities", status_code=status.HTTP_201_CREATED)
def create_city(...):
    return {...}
```

`status.HTTP_201_CREATED` is just the integer `201` with a readable name. `status_code=201` is
identical and shorter; the named constant makes reviews easier. Either is fine — be consistent.

### Errors: `HTTPException`

To fail deliberately, **raise**, don't return:

```python
from fastapi import HTTPException

@app.get("/cities/{name}")
def read_city(name: str):
    if name not in KNOWN_CITIES:
        raise HTTPException(status_code=404, detail=f"City {name!r} not found")
    return {"city": name}
```

| Token | Meaning |
|---|---|
| `raise` | Not `return`. FastAPI catches this exception and converts it to a response |
| `status_code=404` | The code the caller receives |
| `detail=` | Becomes the JSON body: `{"detail": "City 'Zwolle' not found"}` |
| `{name!r}` | f-string conversion flag: use `repr()`, so the value appears **in quotes** |

Why raise rather than return? Because errors usually happen deep inside helper functions, several
calls below the handler. `return` only exits one function; `raise` unwinds all of them. This is the
same reason your Module 2 `fetch.py` used `response.raise_for_status()` instead of checking a code
and returning a flag.

`{name!r}` is a small thing that pays off in logs: `City 'Zwolle ' not found` immediately shows the
trailing space that `City Zwolle  not found` hides.

> 🎯 **Remember this** — `status_code=` in the decorator sets the happy path; `raise HTTPException`
> sets the unhappy one. Raise, never return, your errors.

---

## 7. Organising: `APIRouter`

One file is fine today. It is not fine at thirty endpoints. `APIRouter` is a **sub-menu** you can
write in its own file and mount onto the main app.

```python
# routers/weather.py
from fastapi import APIRouter

router = APIRouter(prefix="/weather", tags=["weather"])

@router.get("/daily")          # final path: /weather/daily
def read_daily(): ...
```

```python
# main.py
from fastapi import FastAPI
from routers import weather

app = FastAPI()
app.include_router(weather.router)
```

| Token | Meaning |
|---|---|
| `APIRouter()` | A registry, like `FastAPI()`, but not runnable on its own |
| `prefix="/weather"` | Prepended to every path in this router. **No trailing slash** |
| `tags=["weather"]` | Groups these endpoints under a heading in `/docs` |
| `@router.get` | Note: `router`, not `app` |
| `app.include_router(...)` | Copies every route from the router into the real app |

You'll use exactly this structure in the project, so the shape is worth recognising now.

---

## 🔁 Spaced review

<details>
<summary>1. (Day 1) A caller sends a syntactically valid request whose <code>limit</code> is 900 when your maximum is 100. Which status code, and whose fault?</summary>

`422 Unprocessable Entity`. The shape was fine and the values were not, which is the caller's fault —
a `4xx`. Not `400` (that's for malformed requests), and definitely not `500`, which would page you
for someone else's typo. FastAPI returns this automatically from `Query(le=100)`.
</details>

<details>
<summary>2. (Day 1) Why is <code>GET /cities/delete/Utrecht</code> a bad design in two separate ways?</summary>

First, it puts a **verb in the path**; REST says the verb belongs in the method, so it should be
`DELETE /cities/Utrecht`. Second, and worse, it makes a **destructive operation reachable by GET**,
which must be safe. Link previewers, crawlers, and browser prefetch all fire GETs unprompted, so
this design will eventually delete data with nobody having clicked anything.
</details>

<details>
<summary>3. (Module 2) Your handler will query <code>marts.weather_weekly</code>. Which layer built that table, and is it safe to drop it?</summary>

`sql/20_marts_weather.sql` builds it from `staging.weather_clean`, which `sql/10_staging_weather.sql`
builds from `raw.weather_daily`. Staging and marts are **rebuilt from scratch every run**, so yes —
dropping marts is safe, the next `python -m pipeline.run` recreates it. Dropping **raw** is not safe:
raw is the evidence locker and only ever accumulates.
</details>

---

## 📌 Day 2 on one screen

```python
from fastapi import FastAPI, Query, HTTPException, status
app = FastAPI()                       # the registry

@app.get("/cities/{name}")            # decorator = write a row in the routing table
def read_city(                        # "path operation function"
    name: str,                        # in the path  -> PATH param
    limit: int = Query(10, ge=1, le=100),   # not in path -> QUERY param, with rules
):
    if unknown:
        raise HTTPException(404, detail="...")   # RAISE errors
    return {"city": name}             # dict -> JSON, automatically

# run:   uvicorn main:app --reload        module:variable
# docs:  /docs  /redoc  /openapi.json     free, always accurate
```

| Rule | |
|---|---|
| Type hint = doorman | converts, validates, documents |
| In path / not in path | path param / query param |
| Default value | makes a parameter optional |
| Specific routes first | `/users/me` above `/users/{id}` |
| `0.0.0.0` | needed once you're in Docker (Day 7) |

---

## ➡️ Next

Notebook **[04_fastapi_practice.ipynb](04_fastapi_practice.ipynb)** — build the app, break it on
purpose, read the 422s, and hit the route-order bug so it never catches you in production.

Day 3 replaces loose dicts with **Pydantic models**, and the doorman gets much stricter.
