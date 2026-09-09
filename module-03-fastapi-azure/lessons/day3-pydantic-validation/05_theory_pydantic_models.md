# Day 3 — Pydantic: The Order Form and the Plating Standard

**Time:** ~2.5 h · **Prerequisite:** Day 2 (routes, path/query params)

Yesterday every response was a loose `dict` and every input was a single scalar. That doesn't survive
contact with real data. Today you give both directions a **shape**.

---

## 🧠 Before you read — predict first

1. Your `GET /users/42` handler fetches a row from the database and returns it as a dict. What could
   go badly wrong when that table later gains a `password_hash` column?
2. Day 1 said JSON has no idea what a `Decimal` or a `date` is, and your `marts` tables are full of
   `NUMERIC`. Who should convert them, and where?
3. If a caller POSTs `{"city": "Utrecht", "lat": "fifty-two"}`, at what point in your code would you
   like that to fail?

---

## 1. The problem with dicts

```python
@app.post("/cities")
def create_city(payload: dict):
    name = payload["name"]                 # KeyError if missing -> 500
    lat = float(payload["latitude"])       # ValueError if "abc" -> 500
    save(name, lat)
```

Every line is a landmine, and every landmine detonates as a **500**. Remember Day 1: `5xx` means
*my* fault. But a caller sending `{"nmae": "Utrecht"}` is *their* fault, and they should get a `422`
that names the typo. Instead they get "Internal Server Error" and you get paged.

The deeper problem is that the dict is a **promise nobody checked**. Nothing in the signature says
what `payload` contains. Six months later, neither the caller, the docs, nor your editor can tell
you. The bug is not the missing `try/except`; the bug is that the shape is invisible.

### The fix: declare the shape

```python
from pydantic import BaseModel

class CityIn(BaseModel):
    name: str
    latitude: float
    longitude: float

@app.post("/cities")
def create_city(city: CityIn):
    save(city.name, city.latitude)     # both guaranteed to exist and be the right type
```

Now the doorman from Day 2 checks the whole party at once. Your function body runs only if every
field is present and convertible. Malformed input never reaches your code — it's rejected at the
door with a `422` naming exactly what was wrong.

> 🎯 **Remember this** — a Pydantic model is the **order form**. The kitchen never sees an order that
> hasn't been filled in correctly.

---

## 2. `BaseModel`, token by token

```python
from pydantic import BaseModel

class CityIn(BaseModel):
    name: str
    latitude: float
    longitude: float
    country: str = "NL"
    population: int | None = None
```

| Token | Meaning |
|---|---|
| `class CityIn(...)` | An ordinary Python class |
| `(BaseModel)` | **Inherits** from Pydantic's base. This is what activates all the machinery |
| `name: str` | A **field**. No default → **required** |
| `country: str = "NL"` | Has a default → **optional**; absent input becomes `"NL"` |
| `population: int \| None = None` | Optional *and* allowed to be explicitly null |

Note there is no `def __init__`, no `self`, no assignment. You are writing **declarations**, not
code — a description of the shape. Pydantic reads the class body's annotations and generates the
constructor, the validator, the serialiser, and the JSON schema from them.

Two spellings that look similar and are not:

```python
population: int | None            # required, but may be null.   {"population": null} ✅  {} ❌
population: int | None = None     # optional and may be null.    {"population": null} ✅  {} ✅
```

The **type** controls what values are allowed. The **default** controls whether the key may be
missing. Beginners conflate these constantly; they are independent knobs.

Using the model:

```python
c = CityIn(name="Utrecht", latitude=52.09, longitude=5.12)
c.name              # "Utrecht"        - attribute access, not c["name"]
c.country           # "NL"             - the default filled itself in
c.model_dump()      # {"name": "Utrecht", ...}  -> a plain dict
c.model_dump_json() # '{"name": "Utrecht", ...}' -> a JSON string
CityIn.model_validate({"name": "Utrecht", "latitude": 52.09, "longitude": 5.12})   # from a dict
```

> ⚠️ **Pydantic v1 vs v2.** You will find older code and older blog posts using `.dict()`,
> `.json()`, and `parse_obj()`. Those are **v1**. This course uses **v2**, where they are
> `model_dump()`, `model_dump_json()`, and `model_validate()`. If a snippet from the internet calls
> `.dict()` on a model, it's written for a version you are not running.

### 🔁 Recall check

<details>
<summary>Which of these are required, and which accept an explicit <code>null</code>?<br><code>a: int</code> · <code>b: int = 0</code> · <code>c: int | None</code> · <code>d: int | None = None</code></summary>

| Field | Key may be missing? | Value may be `null`? |
|---|---|---|
| `a: int` | ❌ required | ❌ no |
| `b: int = 0` | ✅ optional | ❌ no |
| `c: int \| None` | ❌ required | ✅ yes |
| `d: int \| None = None` | ✅ optional | ✅ yes |

`c` is the interesting one: the caller **must** send the key, but is allowed to send `null` in it.
That's how you express "you have to tell me, and 'nothing' is a valid answer."
</details>

---

## 3. Request bodies

Day 2's rule was: *in the path → path param, not in the path → query param.* Pydantic adds the
third and final case:

> If a parameter's type is a **Pydantic model**, FastAPI reads it from the **request body**.

```python
@app.post("/cities", status_code=201)
def create_city(city: CityIn):
    return {"created": city.name}
```

You didn't say "body" anywhere. The type said it. Now the complete rule:

| Parameter type | Comes from |
|---|---|
| Name appears in the path | **Path** |
| Scalar (`int`, `str`, `bool`, `date`…) not in the path | **Query string** |
| Pydantic model | **Body** |
| `Depends(...)` | A dependency (Day 4) |

And these combine freely:

```python
@app.put("/cities/{name}")
def replace_city(name: str, city: CityIn, notify: bool = False):
    #             ^ path        ^ body           ^ query
    ...
```

One signature, three sources, no configuration. This is the payoff of "type hints are the
specification".

### What a validation failure looks like

`POST /cities` with `{"name": "Utrecht", "latitude": "fifty-two"}`:

```json
{
  "detail": [
    {
      "type": "float_parsing",
      "loc": ["body", "latitude"],
      "msg": "Input should be a valid number, unable to parse string as a number",
      "input": "fifty-two"
    },
    {
      "type": "missing",
      "loc": ["body", "longitude"],
      "msg": "Field required"
    }
  ]
}
```

Read it carefully, because this is the answer to prediction question 3:

- Status is **`422`**, automatically. You wrote no error handling.
- `detail` is a **list** — Pydantic reports **every** problem at once, not just the first. Callers
  fix their request in one round trip instead of five.
- `loc` walks from the outside in: `["body", "latitude"]`. For nested models it grows:
  `["body", "location", "lat"]`. For a list it uses indices: `["body", "cities", 2, "name"]`.
- `input` echoes what you actually sent, which is how you spot the invisible trailing space.

> 🎯 **Remember this** — model in the signature = body. Failures come back as a **list** of
> `{type, loc, msg, input}`, and `loc` is a breadcrumb trail to the exact field.

---

## 4. `Field`: constraints and documentation

`Field` is to model attributes what `Query` was to query parameters.

```python
from pydantic import BaseModel, Field

class CityIn(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="City name")
    latitude: float = Field(ge=-90, le=90, description="Degrees north")
    longitude: float = Field(ge=-180, le=180)
    population: int | None = Field(default=None, gt=0)
```

| Constraint | Applies to | Meaning |
|---|---|---|
| `gt` / `ge` | numbers | greater than / greater than or equal |
| `lt` / `le` | numbers | less than / less than or equal |
| `min_length` / `max_length` | str, list | length bounds |
| `pattern` | str | must match this regular expression |
| `default` | anything | the value when omitted |
| `description` / `examples` | anything | shown in `/docs`, ignored at runtime |

`Field(ge=-90, le=90)` on latitude replaces an `if` you would otherwise have to write, test, and
remember to keep in sync with the documentation. Here it *is* the documentation.

### Custom rules: `field_validator`

When a constraint can't be expressed declaratively, write a function:

```python
from pydantic import field_validator

class CityIn(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def strip_and_titlecase(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be blank")
        return v.title()
```

| Token | Meaning |
|---|---|
| `@field_validator("name")` | Run this for the field `name`, after its type is checked |
| `@classmethod` | Required by Pydantic v2. It receives the class, not an instance |
| `cls` | The class. You rarely use it |
| `v` | The value being validated |
| `raise ValueError(...)` | How you reject. Pydantic converts it into a `422` entry |
| `return v.title()` | **The return value replaces the field.** Validators may transform |

That last line is the surprise: a validator is also a *normaliser*. `" utrecht "` becomes
`"Utrecht"` before your handler ever sees it, so you clean data once, at the door, rather than in
every function that touches it.

Note you `raise ValueError`, **not** `HTTPException`. Pydantic doesn't know about HTTP; FastAPI
translates. Keeping your models HTTP-free is what lets you reuse them in a CLI or a background job.

> 🎯 **Remember this** — `Field(...)` for declarative rules, `@field_validator` for logic, and a
> validator's **return value replaces the field**.

### 🔁 Recall check

<details>
<summary>Write a model for a weather query with a required city (1–100 chars), an optional <code>min_temp</code> that must be above −100, and a <code>from_date</code> that must not be in the future.</summary>

```python
from datetime import date
from pydantic import BaseModel, Field, field_validator

class WeatherQuery(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    min_temp: float | None = Field(default=None, gt=-100)
    from_date: date | None = None

    @field_validator("from_date")
    @classmethod
    def not_in_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("from_date cannot be in the future")
        return v
```

The `if v is not None` guard matters: validators run on `None` too when the field is optional, and
comparing `None > date` raises a `TypeError`, which surfaces as a `500` rather than a clean `422`.
</details>

---

## 5. `response_model`: the plating standard

Everything so far guarded the way **in**. This guards the way **out**, and it is the answer to
prediction question 1.

```python
class UserOut(BaseModel):
    id: int
    email: str
    # note what is NOT here

@app.get("/users/{user_id}", response_model=UserOut)
def read_user(user_id: int):
    row = db.fetch_user(user_id)     # dict with id, email, password_hash, internal_notes
    return row                        # returning ALL of it
```

The response contains **only `id` and `email`**. `response_model` doesn't just describe the output —
it **filters** it. Every field not declared is dropped on the way out.

This is a security control, not a formatting nicety. The realistic failure it prevents:

> Someone adds a `password_hash` column. Every handler that returned `dict(row)` now leaks password
> hashes to the internet. Nothing in the code changed. No test failed. No error was logged.

With `response_model`, the new column simply isn't in `UserOut`, so it isn't in the response. The
model is an **allow-list**, and allow-lists fail closed.

That is the plating standard: the kitchen may produce whatever it likes, but only what's on the
standard leaves the pass.

`response_model` does four jobs:

1. **Filters** — drops undeclared fields.
2. **Converts** — `Decimal` → number, `date` → `"2026-09-01"`, `UUID` → string. Prediction question 2
   answered: *Pydantic converts, at the boundary.*
3. **Validates your own output** — if `id` is `None`, your **server** errors, loudly, in development,
   rather than shipping a broken payload.
4. **Documents** — `/docs` shows the exact response shape.

### Reading database rows: `from_attributes`

A SQLAlchemy row is an object with attributes, not a dict. Tell the model to read attributes:

```python
class WeatherOut(BaseModel):
    model_config = {"from_attributes": True}

    city: str
    obs_date: date
    temp_max_c: float
```

| Token | Meaning |
|---|---|
| `model_config = {...}` | Pydantic v2's settings dict. (v1 used an inner `class Config`) |
| `"from_attributes": True` | Also accept objects, reading `obj.city` instead of `obj["city"]` |

Now `WeatherOut.model_validate(row)` works on a SQLAlchemy row directly, and with
`response_model=WeatherOut` FastAPI does it for you. `Decimal("21.40")` from a `NUMERIC` column
lands in the JSON as `21.4` without a single conversion line in your handler — the trap from Day 1,
closed.

> 🎯 **Remember this** — `response_model` is an **allow-list** that filters, converts, validates and
> documents. Undeclared fields cannot leak.

### The In/Out pair

The standard shape, which you'll use in the project:

```python
class CityBase(BaseModel):          # what both directions share
    name: str
    latitude: float
    longitude: float

class CityIn(CityBase):             # what the caller may send
    pass

class CityOut(CityBase):            # what we send back
    model_config = {"from_attributes": True}
    id: int                         # server-assigned: caller must NOT send it
    created_at: datetime            # server-assigned
```

The asymmetry is the point. `id` and `created_at` belong in the response and must be impossible to
supply in a request — otherwise a caller can choose their own primary key.

---

## 6. Nested models and lists

Models compose. A field's type can be another model.

```python
class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class CityIn(BaseModel):
    name: str
    location: Location                # nested object
    tags: list[str] = []              # array of strings
    neighbours: list["CityIn"] = []   # even recursive, if you like
```

Accepting:

```json
{"name": "Utrecht", "location": {"lat": 52.09, "lon": 5.12}, "tags": ["central"]}
```

Validation recurses, and `loc` records the full path: a bad `lat` reports
`["body", "location", "lat"]`.

To return a list, annotate the response model as a list:

```python
@app.get("/cities", response_model=list[CityOut])
def list_cities():
    return db.all_cities()
```

⚠️ `tags: list[str] = []` uses a **mutable default**, which in ordinary Python is the classic shared-
state bug. Pydantic is safe here: it deep-copies defaults per instance. In a plain function
signature, `def f(x=[])` remains a bug — the exemption is Pydantic's, not Python's.

---

## 🔁 Spaced review

<details>
<summary>1. (Day 2) Where do <code>name</code>, <code>city</code>, and <code>notify</code> come from in <code>def f(name: str, city: CityIn, notify: bool = False)</code> on route <code>/cities/{name}</code>?</summary>

`name` → **path** (it appears in the route). `city` → **body** (it's a Pydantic model).
`notify` → **query** (a scalar not in the path, with a default, so optional).
</details>

<details>
<summary>2. (Day 1) Your endpoint returns <code>200</code> with <code>{"detail": "not found"}</code> when a city is missing. What's wrong?</summary>

The **status code lies**. `200` means success, so every automated caller — retry logic, caches,
monitoring, client libraries — will treat a missing city as a successful result and try to read
fields that aren't there. Status codes are the machine-readable part of the answer; the body is only
for humans. Raise `HTTPException(404, ...)` instead.
</details>

<details>
<summary>3. (Module 2) Your <code>marts.weather_weekly</code> has a <code>NUMERIC</code> average temperature. Trace what happens to that value from database to JSON.</summary>

Postgres `NUMERIC` → psycopg2/SQLAlchemy hands it to Python as a **`Decimal`** (chosen deliberately
to avoid float rounding on money and measurements) → `json.dumps` **cannot serialise `Decimal`** and
raises `TypeError` → but with `response_model` declaring `avg_temp_c: float`, Pydantic converts it at
the boundary and the caller receives `21.4`.

Nothing in your handler had to know. That's the boundary doing its job.
</details>

---

## 📌 Day 3 on one screen

```python
from pydantic import BaseModel, Field, field_validator

class CityIn(BaseModel):                       # THE ORDER FORM (in)
    name: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    country: str = "NL"                        # default => optional

    @field_validator("name")
    @classmethod
    def clean(cls, v): return v.strip().title()   # return value REPLACES the field

class CityOut(CityIn):                         # THE PLATING STANDARD (out)
    model_config = {"from_attributes": True}   # read ORM objects, not just dicts
    id: int                                    # server-assigned, never accepted as input

@app.post("/cities", response_model=CityOut, status_code=201)
def create(city: CityIn): ...                  # model in signature => request BODY
```

| | |
|---|---|
| Required vs optional | decided by the **default**, not the type |
| `int \| None` vs `int \| None = None` | may be null · may be absent *and* null |
| Errors | `422`, a **list**, `loc` is a breadcrumb to the field |
| `response_model` | filters · converts · validates · documents. **Allow-list** |
| v2 not v1 | `model_dump()` `model_validate()`, not `.dict()` `.parse_obj()` |

---

## ➡️ Next

Notebook **[06_pydantic_practice.ipynb](06_pydantic_practice.ipynb)** — build the models, read real
`422` payloads field by field, and watch `response_model` refuse to leak a password hash.

Day 4 connects the API to your Module 2 database using **dependency injection**, and you'll see why
that makes testing easy on Day 5.
