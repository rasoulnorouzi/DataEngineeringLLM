# Day 1 — HTTP & REST From Zero

**Time:** ~2 h · **Prerequisite:** none (Module 2 helps but isn't required for today)

By the end of this you can read a raw HTTP request and response out loud, explain what every line
of it means, and say why an API is just "a restaurant with a written menu".

---

## 🧠 Before you read — predict first

Write your guesses down. Guessing *before* being told is what makes today stick; the research word
for it is the **generation effect**, and it is worth more than re-reading this page twice.

1. When you type `example.com` in a browser, your computer sends some text to another computer.
   Roughly what does that text say?
2. `404` is famous. Without looking it up: what do you think `201` and `503` mean?
3. Your Module 2 pipeline wrote weather rows into Postgres. If a colleague in another country wants
   those rows, why not just give them the database password?

Keep these; you'll grade yourself at the bottom.

---

## 1. Why APIs exist at all

You finished Module 2 with a database full of Dutch weather. It is genuinely useful data. Now
someone wants it — a dashboard, a mobile app, a colleague's notebook, an LLM agent (Module 6, that
one is you).

### The bad way

Hand out the database password.

```
host: my-db.example.com   user: student   password: student123
```

Five things go wrong immediately:

| What goes wrong | Why |
|---|---|
| They can read **everything** | The password opens every table, including ones they shouldn't see |
| They can **write** | One bad `DELETE` and your pipeline's raw layer is gone |
| They must understand your schema | `staging.weather_clean` vs `marts.weather_weekly`? They don't know |
| You can never refactor | Rename a column and every consumer breaks silently |
| Only SQL-speakers can use it | Front-end developers, phone apps, and agents don't speak psycopg2 |

### The good way

Put a **counter** in front of the data. You decide what can be asked for, in what shape, by whom.
Behind the counter you can rename tables, switch databases, add caching — and nobody notices.

That counter is an **API**: Application Programming Interface. A programme-to-programme interface,
as opposed to a UI, which is a programme-to-human interface.

> 🎯 **Remember this** — a UI is for humans, an API is for programmes. Both are counters; only the
> customer differs.

### 🍽️ The metaphor for this whole module: the restaurant

We'll ride this one all the way to Azure, so let it settle in now.

| Restaurant | API |
|---|---|
| The **menu** | The API docs — what you're allowed to order |
| An **item on the menu** | An **endpoint** — one thing you can ask for |
| **Ordering** ("one soup, no bread") | An HTTP **request** |
| The **waiter's reply** ("here you go" / "we're out of soup") | An HTTP **response** |
| The **kitchen** | Your database and business logic |
| You never walk into the kitchen | Callers never touch your database |

The last row is the whole point. The kitchen can be rebuilt overnight; as long as the menu still
says "soup", the customer's experience is unchanged.

### 🔁 Recall check

<details>
<summary>Your company's API serves customer orders. The team migrates from Postgres to a different database over a weekend. Should any caller's code change? Why or why not?</summary>

**No.** Callers talk to the menu, not the kitchen. They send `GET /orders/42` and receive JSON. What
storage produced that JSON is invisible to them — that invisibility *is* the value of putting an API
in front of data. If callers *did* have to change, that's a sign the API was leaking database
details it should have hidden (returning raw column names, or exposing SQL directly).
</details>

---

## 2. HTTP: the language spoken at the counter

**HTTP** = HyperText Transfer Protocol. A protocol is just an agreed format so two programmes that
have never met can understand each other. HTTP's format is startlingly simple: **it is plain text.**

Here is a complete, real request. Nothing is hidden:

```http
GET /weather/daily?city=Amsterdam&limit=2 HTTP/1.1
Host: api.example.com
Accept: application/json
User-Agent: curl/8.5.0

```

Line by line — every token:

| Piece | Name | What it does |
|---|---|---|
| `GET` | **method** | The verb. What do you want done? (see §3) |
| `/weather/daily` | **path** | Which item on the menu |
| `?city=Amsterdam&limit=2` | **query string** | Options on that item. `?` starts it, `&` separates pairs, `=` joins key to value |
| `HTTP/1.1` | **version** | Which edition of the protocol |
| `Host: api.example.com` | **header** | Metadata: which site (one server hosts many) |
| `Accept: application/json` | **header** | "Reply in JSON, please" |
| `User-Agent: curl/8.5.0` | **header** | Who is asking |
| *(blank line)* | **separator** | **Required.** Marks the end of headers. Below it would come the body |

That's it. A request is: **method + path + headers + optional body.** A browser, `curl`, Python's
`requests`, and your phone all send exactly this shape of text.

And the reply:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 122

{"city": "Amsterdam", "days": [{"date": "2026-09-01", "temp_max_c": 21.4}]}
```

| Piece | Name | What it does |
|---|---|---|
| `HTTP/1.1` | version | Same protocol edition |
| `200` | **status code** | The verdict, as a number (see §4) |
| `OK` | reason phrase | Human-readable label for the number. Decorative — code is what matters |
| `Content-Type: application/json` | header | "What I'm sending you is JSON" |
| `Content-Length: 122` | header | How many bytes the body is |
| *(blank line)* | separator | Ends the headers |
| `{...}` | **body** | The actual payload |

> 🎯 **Remember this** — request = *method + path + headers + body*; response = *status + headers +
> body*. Four parts each, and the blank line always separates headers from body.

### 🔁 Recall check

<details>
<summary>In the request above, which part would you change to ask for Rotterdam instead of Amsterdam — and which part would you change to ask for the <em>weekly</em> summary instead of daily?</summary>

- Rotterdam: the **query string** — `?city=Rotterdam&limit=2`. It's an *option on the same dish*.
- Weekly: the **path** — `/weather/weekly`. It's a *different dish*.

That distinction (path = which resource, query = how you want it filtered) is the single most
useful instinct in API design, and it comes back on Day 2 as path parameters vs query parameters.
</details>

---

## 3. Methods: the verbs

The method says what you want done. There are many; five carry 99% of real traffic.

| Method | Restaurant | Meaning | Has a body? | Safe? | Idempotent? |
|---|---|---|---|---|---|
| `GET` | "Bring me the soup" | Read something | No | ✅ yes | ✅ yes |
| `POST` | "Make me a new pizza" | Create something new | Yes | ❌ no | ❌ no |
| `PUT` | "Replace my order entirely" | Replace a whole resource | Yes | ❌ no | ✅ yes |
| `PATCH` | "Actually, hold the onions" | Change part of a resource | Yes | ❌ no | ❌ usually not |
| `DELETE` | "Take it away" | Remove a resource | No | ❌ no | ✅ yes |

Two words in that table are load-bearing:

**Safe** = it doesn't change anything. A `GET` must never modify data. If your `GET /delete-user/5`
deletes a user, you have built a trap: browsers, crawlers, and link previewers fire `GET` requests
speculatively, and one day something will crawl your links and wipe your database.

**Idempotent** = doing it twice has the same effect as doing it once.

You already met this word in Module 2. `ON CONFLICT (city, obs_date) DO UPDATE` made your loader
idempotent — the "light switch" you can flip up twice and it's still just *up*. Same idea here:
`DELETE /orders/42` twice leaves you with exactly one outcome (order 42 is gone), but
`POST /orders` twice leaves you with **two orders**. That is precisely why double-clicking a
"Pay now" button is dangerous and double-clicking "Refresh" is not.

> 🎯 **Remember this** — GET is safe *and* idempotent, POST is neither, DELETE and PUT are
> idempotent but not safe. The light switch from Module 2 is the same concept, wearing a different
> hat.

### 🔁 Recall check

<details>
<summary>A checkout page fires <code>POST /payments</code>. The network hiccups and the client isn't sure the request arrived, so it retries. What can go wrong, and what does the idempotency table tell you to do about it?</summary>

The customer may be charged **twice** — `POST` is not idempotent, so the second request creates a
second payment.

The table tells you the fix has to come from *you*, because the method won't provide it. The
standard move is an **idempotency key**: the client generates a unique id once, sends it as a header
on both attempts, and the server stores it and refuses to process the same key twice. That is
exactly the `ON CONFLICT` trick from Module 2, lifted up to the HTTP layer — a primary key on
"requests I have already honoured".
</details>

---

## 4. Status codes: the verdict in three digits

The **first digit** is the whole story. Memorise the five families and you can guess the rest.

| Family | Meaning | Mnemonic |
|---|---|---|
| **1xx** | "Hold on, still going" | Rare. Ignore for now |
| **2xx** | ✅ "Here you go" | It worked |
| **3xx** | ↪️ "It's over there" | Redirect, go look elsewhere |
| **4xx** | 🙋 **You** messed up | Your order was wrong — fix the request |
| **5xx** | 🔥 **We** messed up | The kitchen is on fire — the request was fine |

That 4xx/5xx split is the one that matters day to day, and it decides who gets woken up at 3 a.m.
**4xx is the customer's fault, 5xx is the kitchen's fault.** If your service returns `500` when
someone sends a malformed date, you will be paged for a bug that isn't yours. Return `422` instead
and the caller fixes their own request.

The ones you will actually use:

| Code | Name | Use it when |
|---|---|---|
| `200` | OK | A successful `GET` (or any success with a body) |
| `201` | Created | A successful `POST` that made something new |
| `204` | No Content | Success, and there's deliberately nothing to send back (a `DELETE`) |
| `400` | Bad Request | The request is malformed in a general way |
| `401` | Unauthorized | **You haven't proved who you are.** (Misnamed — it means *unauthenticated*) |
| `403` | Forbidden | You proved who you are, and you're still not allowed |
| `404` | Not Found | No such resource |
| `422` | Unprocessable Entity | The shape was right but the values are invalid. **FastAPI's favourite** |
| `429` | Too Many Requests | Rate limited, slow down |
| `500` | Internal Server Error | Your code raised an unhandled exception |
| `503` | Service Unavailable | The service is up but a dependency (the database) isn't |

401 vs 403 is a classic interview question. The one-liner: **401 = "who are you?", 403 = "I know
exactly who you are, and no."**

> 🎯 **Remember this** — `4xx` is your fault, `5xx` is my fault. `201` means *I made something*,
> `422` means *your values are wrong*.

### 🔁 Recall check

<details>
<summary>Grade your prediction from the top of the page: what do <code>201</code> and <code>503</code> mean? And which code should <code>POST /cities</code> return when the body is valid JSON but <code>latitude</code> is 500?</summary>

- `201 Created` — a successful creation.
- `503 Service Unavailable` — the service can't serve right now, typically a dependency is down.
- Latitude 500: **`422`**. The JSON parsed fine (so not `400`), the caller is at fault (so not
  `5xx`), and the problem is a *value* failing validation. On Day 3 you'll see FastAPI return this
  automatically, with a message naming the exact field — for free.
</details>

---

## 5. REST: six letters of convention

**REST** = REpresentational State Transfer. Grand name, modest idea: a set of *conventions* for
laying out an HTTP API so that other developers can guess how it works without reading a manual.

REST is not a law, a library, or a standard you can validate against. It is a style. Following it
means your API is **predictable**, and predictability is most of usability.

### The core rule: nouns in the path, verbs in the method

The path names a **resource** (a thing). The method says what to do to it.

```
❌  POST /getUserById?id=42          verb in the path, method meaningless
❌  GET  /deleteCity?name=Utrecht    a GET that destroys data. A trap
❌  POST /api/doWeatherUpdate        what is a "doWeatherUpdate"?

✅  GET    /users/42                 read user 42
✅  DELETE /cities/Utrecht           remove Utrecht
✅  POST   /cities                   create a city (details in the body)
✅  GET    /cities                   list cities
✅  PATCH  /cities/Utrecht           edit part of Utrecht
```

Read the good column aloud. Each line is a sentence: *verb, then noun.* You never had to be told
what `DELETE /cities/Utrecht` does.

### The shapes that recur

Two levels, and you'll use them constantly:

| Pattern | Name | Returns |
|---|---|---|
| `/cities` | **collection** | A list |
| `/cities/Utrecht` | **item** (or "resource") | One thing |
| `/cities/Utrecht/observations` | **sub-collection** | A list belonging to one item |

Filtering, sorting, and paging go in the **query string**, never the path, because they are options
rather than identities:

```
GET /weather/daily?city=Utrecht&from=2026-09-01&to=2026-09-07&limit=50
```

> 🎯 **Remember this** — **path = which thing, query = how you want it.** If removing the parameter
> would still leave a sensible request, it belongs in the query string.

### 🔁 Recall check

<details>
<summary>Design the path + method for: "list every weather observation for Rotterdam in August 2026, newest first, 20 per page."</summary>

```
GET /weather/daily?city=Rotterdam&from=2026-08-01&to=2026-08-31&sort=-date&limit=20&offset=0
```

Points to notice:
- `GET`, because it reads and changes nothing.
- `/weather/daily` is the resource; **Rotterdam is a filter, not the resource** — you're asking for
  daily observations, narrowed to one city.
- Everything else is an option, so everything else is query string.
- `sort=-date` with a leading minus for descending is a widespread convention, not a rule.
- `limit`/`offset` is the simplest paging scheme. You will build exactly this in the project.

An acceptable alternative is `/cities/Rotterdam/weather?...`, treating the observations as a
sub-collection of the city. Both are RESTful. Pick one and be consistent — consistency is the point.
</details>

---

## 6. JSON: the plate everything is served on

**JSON** = JavaScript Object Notation. Despite the name it belongs to no language; it is the default
body format for APIs because every language can read it and humans can too.

Six types, and that is the entire specification:

```json
{
  "city": "Amsterdam",              
  "temp_max_c": 21.4,               
  "station_active": true,           
  "closed_reason": null,            
  "tags": ["knmi", "coastal"],      
  "location": { "lat": 52.37, "lon": 4.90 }
}
```

| Line | Type |
|---|---|
| `"Amsterdam"` | **string** — double quotes only, never single |
| `21.4` | **number** — no distinction between int and float |
| `true` | **boolean** — lowercase, unlike Python's `True` |
| `null` | **null** — lowercase, and this is Python's `None` |
| `[...]` | **array** — Python calls it a list |
| `{...}` | **object** — Python calls it a dict |

Four rules that cause almost every JSON error you will ever hit:

1. **Double quotes.** `{'city': 'x'}` is a Python dict printed out, not JSON.
2. **Keys are always strings.** `{1: "a"}` is invalid.
3. **No trailing comma.** `{"a": 1,}` is invalid — this one bites everybody.
4. **No comments.** The empty space after the commas above is me being tidy; a `//` would be invalid.

Python translates automatically:

| Python | JSON |
|---|---|
| `dict` | object |
| `list`, `tuple` | array |
| `str` | string |
| `int`, `float` | number |
| `True` / `False` | `true` / `false` |
| `None` | `null` |
| `datetime`, `Decimal` | ❌ **nothing** — you must convert these yourself |

That last row is a real trap and you already have the ingredients for it: your Module 2 `marts`
tables hold `NUMERIC` columns, which SQLAlchemy hands you as `Decimal`, which `json.dumps` refuses
to serialise. On Day 3 you'll watch Pydantic solve this for you without you asking.

> 🎯 **Remember this** — JSON has six types, uses double quotes, forbids trailing commas, and has no
> idea what a date or a `Decimal` is.

---

## 7. Seeing it for real

Three ways to send an HTTP request by hand. Try each in the notebook.

```bash
# curl: the universal tool. -s = silent, -i = include response headers
curl -s -i "https://api.open-meteo.com/v1/forecast?latitude=52.37&longitude=4.90&current=temperature_2m"
```

| Flag | Meaning |
|---|---|
| `-s` | Silent: hide the progress meter |
| `-i` | Include the response headers, not just the body |
| `-X POST` | Set the method (default is GET) |
| `-H "K: V"` | Add a header |
| `-d '{...}'` | Send a body (and implies `POST`) |

```python
# Python: the requests library, which you used in Module 2's fetch.py
import requests
r = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={"latitude": 52.37, "longitude": 4.90, "current": "temperature_2m"},
    timeout=30,
)
r.status_code    # 200      -> the number
r.headers        # dict     -> the response headers
r.json()         # dict     -> body, parsed from JSON
r.text           # str      -> body, unparsed
r.raise_for_status()   # raise an exception if status is 4xx or 5xx
```

Note `params={...}`: you hand `requests` a dict and it builds `?latitude=52.37&longitude=4.9` for
you, including escaping awkward characters. Never build a query string by gluing strings together —
a city called `Den Haag` has a space in it, and spaces are illegal in URLs.

> 🎯 **Remember this** — `r.json()` parses, `r.text` doesn't, and `raise_for_status()` is the one
> line that turns a silent `404` into a loud crash.

---

## 🔁 Spaced review — Module 2, still in there?

Answer before opening the details. This is not filler; retrieving old material is what stops it
decaying.

<details>
<summary>1. What made your Module 2 loader safe to run twice, and what was the analogy?</summary>

`ON CONFLICT (city, obs_date) DO UPDATE` — an upsert keyed on the primary key. Running the pipeline
twice overwrites the same rows instead of duplicating them. The analogy was the **light switch**:
flipping it up when it's already up leaves it up. Today you met the same idea as HTTP idempotency.
</details>

<details>
<summary>2. In what order does <code>transform.py</code> execute the SQL files, and why are they named <code>10_</code> and <code>20_</code>?</summary>

Sorted **filename order**. The numeric prefixes exist to force staging (`10_`) to run before marts
(`20_`), because marts are built *from* staging. The numbers are ordering, not decoration — rename
them carelessly and the pipeline breaks.
</details>

<details>
<summary>3. Which of your Module 2 tests skip when Docker isn't running, and why does that matter?</summary>

The integration tests in `tests/test_db_integration.py` call `pytest.skip` when no database is
reachable. It matters because a green local `pytest` therefore does **not** prove the database path
works — only the scheduled workflow, which runs against a real Postgres service container, proves
that. Green is not always the same as tested.
</details>

---

## 📌 Day 1 on one screen

```
REQUEST                              RESPONSE
  method  GET                          status   200
  path    /weather/daily               headers  Content-Type: application/json
  query   ?city=Amsterdam              body     {"city": "Amsterdam", ...}
  headers Accept: application/json
  body    (only for POST/PUT/PATCH)

METHODS      GET read (safe+idempotent) · POST create (neither)
             PUT replace · PATCH edit · DELETE remove (idempotent)

STATUS       2xx here you go · 3xx it moved · 4xx YOUR fault · 5xx MY fault
             201 created · 204 nothing to return · 401 who are you?
             403 no · 404 no such thing · 422 bad values · 500 I crashed

REST         nouns in the path, verbs in the method
             /cities collection · /cities/Utrecht item
             path = WHICH thing · query = HOW you want it

JSON         6 types · double quotes · no trailing comma · no dates, no Decimal
```

---

## ➡️ Next

Notebook **[02_http_practice.ipynb](02_http_practice.ipynb)** — you'll send real requests to a live
API, read every header, deliberately trigger a 404 and a 422, and turn a badly-designed API into a
RESTful one.

Then Day 2 builds your first FastAPI app, and the menu starts writing itself.
