# Day 7 Theory: HTTP APIs & Ingestion — Where Data Actually Comes From

**Time:** ~1 hour reading, then the practice notebook (`15_ingestion_practice.ipynb`)
**Prerequisites:** Day 6 (ELT, idempotency)

---

## 1. Why This Lesson Exists

Every pipeline starts with an **Extract** step, and in the real world the source is very often an
**HTTP API**: your company's CRM, a payment provider, a government open-data portal. If you can
call an API, parse its JSON, and load it idempotently, you can ingest almost anything.

Today's source: **live Dutch weather data** — free, no registration, and genuinely useful for the
project you're about to build.

---

## 2. What an API Actually Is

**Analogy — the restaurant counter.** A restaurant doesn't let customers into the kitchen. There's
a counter: you place a *structured order* ("one pizza margherita, large"), and you get back a
*structured result*. You don't need to know how the kitchen works, and the kitchen doesn't need to
know who you are.

An **API** (Application Programming Interface) is that counter for software. A **web API** is one
you talk to over HTTP — the same protocol your browser uses. The difference: your browser asks for
web pages (HTML, for humans); your code asks for **data** (JSON, for programs).

### Anatomy of a request

```
https://archive-api.open-meteo.com/v1/archive?latitude=52.10&longitude=5.18&daily=temperature_2m_max
└──────┬──────┘└──────────┬──────────┘└──┬───┘└──────────────────┬─────────────────────────────────┘
     scheme            host           path                query parameters (the "order details")
```

- **Host + path** = which counter, which menu item ("the historical weather archive")
- **Query parameters** (after `?`, separated by `&`) = your order's options: *which location, which
  dates, which variables*
- **Method**: today we only need `GET` ("read data"). `POST`/`PUT`/`DELETE` (writing) arrive in
  Module 3 when you *build* your own API with FastAPI.

### Anatomy of a response

Two parts matter:

1. **Status code** — a three-digit verdict:
   - `200` OK — here's your data
   - `4xx` — *you* messed up (`404` wrong path, `400` bad parameters, `429` slow down!)
   - `5xx` — *they* messed up (server error; retry later)
2. **Body** — the data itself, almost always **JSON**.

**JSON is just Python with different makeup.** `{}` objects ↔ `dict`, `[]` arrays ↔ `list`,
plus strings/numbers/booleans/`null`(→`None`). One method call converts it: `response.json()`.

---

## 3. Calling APIs from Python: `requests`

```python
import requests

response = requests.get(
    "https://archive-api.open-meteo.com/v1/archive",
    params={                              # requests builds the ?a=b&c=d part for you
        "latitude": 52.10,                # De Bilt — home of the KNMI, the Dutch
        "longitude": 5.18,                #   national weather institute
        "start_date": "2026-07-01",
        "end_date": "2026-07-07",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Europe/Amsterdam",
    },
    timeout=30,                           # NEVER call an API without a timeout
)
response.raise_for_status()               # turns 4xx/5xx into a Python exception
data = response.json()                    # JSON body -> Python dict
```

Three professional habits baked in above — make them reflexes:

1. **`params=` dict**, never hand-glued f-strings (handles encoding, stays readable)
2. **`timeout=`** always — otherwise a hanging server hangs your pipeline forever
3. **`raise_for_status()`** immediately — fail loudly at the source, not three steps later with
   confusing `KeyError`s

The response for this call looks like:

```json
{
  "latitude": 52.1,
  "daily": {
    "time":               ["2026-07-01", "2026-07-02", ...],
    "temperature_2m_max": [22.4, 19.8, ...],
    "temperature_2m_min": [12.1, 11.3, ...],
    "precipitation_sum":  [0.0, 4.2, ...]
  }
}
```

Note the shape: **parallel arrays** (column-oriented), not one-object-per-day. Real APIs come in
every shape imaginable; reshaping is *your* job — and it's exactly a `zip()` in Python.

---

## 4. Loading It the ELT Way

Yesterday's rules, applied:

1. **Store raw first.** We insert the API's JSON essentially as-is into `raw.weather_daily`
   (Postgres has a `JSONB` column type that stores JSON and lets you query inside it). If we later
   want a variable we ignored, it's already in the locker.
2. **Upsert on a natural key.** One row per `(city, date)` with
   `ON CONFLICT (city, date) DO UPDATE` — reruns and overlapping fetch windows are harmless.
3. **Fetch an overlapping window.** Each run asks for the **last 7 days** even though we run daily.
   Weather archives *correct* recent values; the overlap + upsert picks corrections up
   automatically, and a weekend of failed runs heals itself on Monday.

This trio — raw JSONB + natural-key upsert + overlapping window — is a production-grade ingestion
pattern, miniaturized.

---

## 5. Being a Polite API Citizen

Open APIs are a commons. The rules (also: how you avoid `429 Too Many Requests`):

- **Ask only for what you need** (7 days, 3 variables — not 10 years of everything, daily)
- **Don't hammer**: a short `time.sleep()` between calls to the same host is plenty at our scale
- **Read the terms**: Open-Meteo is free for non-commercial use, no API key, fair-use limits —
  perfect for us. (The official KNMI Data Platform API is a great stretch goal; it requires a free
  API key — a taste of real-world auth.)
- **Expect failure**: networks flake. Because our load is idempotent, the recovery strategy is
  beautifully simple: *just run it again.*

---

## 6. Summary

- APIs are counters: structured request in (URL + query params), structured JSON out
- Status codes: `200` good, `4xx` your fault, `5xx` their fault
- `requests.get(url, params=..., timeout=...)` + `raise_for_status()` + `.json()` — the whole game
- Load raw JSONB first, upsert on `(city, date)`, fetch overlapping windows — idempotent ingestion
- Be polite: small requests, pauses, read the terms

**Now open `15_ingestion_practice.ipynb`** and ingest real Dutch weather into your Postgres.
