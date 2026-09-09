# Day 7 — The Food Truck: Containerising Your API

**Time:** ~2.5 h · **Prerequisite:** Days 2–6, and `docs/DOCKER_GUIDE.md` from Module 2

In Module 2 you **ran** containers other people built — Postgres, pgAdmin. Today you **build one**,
containing your own application. Different skill, same machinery.

---

## 🧠 Before you read — predict first

1. Your Dockerfile copies your source code and then installs dependencies. You change one line of
   Python and rebuild. Roughly how long should that take — and how long will it actually take?
2. Day 2 mentioned `--host 0.0.0.0` would matter "once you're in Docker". Why?
3. Your image works perfectly. Should the process inside it run as `root`? What could go wrong?

---

## 1. What an image actually is

A **container image** is a filesystem plus a default command. That's it. When you run it, Docker
unpacks that filesystem, isolates it, and runs the command inside.

The restaurant metaphor holds up: an image is a **food truck**. The kitchen, the recipes, the
ingredients, and the instructions are all bolted into one box. Park it anywhere — your laptop, a CI
runner, Azure — and it cooks identically, because it brought its whole world with it.

That's the answer to "works on my machine": there is no *your* machine any more. There's the truck.

| Term | Meaning |
|---|---|
| **Dockerfile** | The recipe for building the truck |
| **Image** | The built truck. Immutable, versioned, shareable |
| **Container** | A running instance of an image. You can run many from one image |
| **Registry** | The depot where trucks are parked and versioned (Day 8: Azure Container Registry) |
| **Layer** | One step of the build, cached independently. The key to fast rebuilds |

---

## 2. A first Dockerfile, token by token

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "insight_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `FROM python:3.12-slim`

Every image starts from another image. This one is the official Python image.

| Tag | Size | Use when |
|---|---|---|
| `python:3.12` | ~1 GB | You need compilers and system libraries |
| `python:3.12-slim` | ~150 MB | **Default choice.** Debian, minus the extras |
| `python:3.12-alpine` | ~50 MB | Tempting, and usually a trap |

The Alpine trap is worth knowing: Alpine uses **musl** instead of **glibc**, so Python wheels
compiled for normal Linux don't work. Pip falls back to building from source, and a 20-second
install becomes a 10-minute compile — for an image that is often *bigger* in the end because it
needed a toolchain. `slim` is the right default.

**Always pin the version.** `FROM python:3.12-slim` and not `FROM python`, or your build silently
moves to a new Python release one morning and something breaks with no commit to blame.

### `WORKDIR /app`

Sets the working directory for every later instruction, creating it if needed. It's `cd`, but it
persists. Without it you'd write absolute paths everywhere and `CMD` would start in `/`.

### `COPY pyproject.toml ./` then `RUN pip install`

Copies from your machine (the **build context**) into the image, then runs a command *at build time*
and saves the result.

`--no-cache-dir` tells pip not to keep its download cache. Inside an image that cache is dead weight
you'd ship forever — worth 40–80 MB.

### `COPY src/ ./src/`

Your application code. **Note that this comes after the install.** That ordering is the whole of §3
and the answer to prediction question 1.

### `EXPOSE 8000`

**Documentation only.** It publishes nothing and opens nothing. It records which port the image
*intends* to serve on, for humans and for tools. Actually reaching the port needs `-p 8000:8000` at
run time. Beginners expect `EXPOSE` to do something; it does not.

### `CMD [...]`

The default command when a container starts. Two forms, and the difference matters:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]     # exec form  ✅
CMD uvicorn main:app --host 0.0.0.0                  # shell form ❌
```

**Exec form** (a JSON array) runs your process directly as PID 1. **Shell form** wraps it in
`/bin/sh -c`, so the shell is PID 1 and your app is a child.

Why that matters: when Docker, Kubernetes, or Azure stops a container it sends `SIGTERM` to PID 1.
In shell form the shell receives it and **does not forward it**, so your app never learns it should
shut down. After a grace period (usually 10 s) it's killed with `SIGKILL` — mid-request, with
connections open. In exec form your app gets the signal, finishes in-flight requests, closes the
pool, and exits cleanly.

Use the JSON array form. Always.

### `--host 0.0.0.0`

Prediction question 2, and it's the most common "my container returns nothing" bug.

Uvicorn defaults to `127.0.0.1` — "accept connections from **this machine** only". Inside a
container, "this machine" is the container's own isolated network namespace. Traffic arriving from
outside is refused, and you get an empty reply with no error in the logs.

`0.0.0.0` means "accept on all interfaces". Inside a container that's what you want. On your laptop
outside a container it's what you *don't* want, which is why the default is what it is.

> 🎯 **Remember this** — `EXPOSE` documents, `-p` publishes. Exec-form `CMD` so signals arrive.
> `--host 0.0.0.0` or the container answers nobody.

---

## 3. Layer caching: why the order of lines is the whole game

Every instruction creates a **layer**. Docker caches layers and reuses them while the inputs to that
instruction haven't changed. **When one layer misses the cache, every layer after it is rebuilt.**

Now compare. The wrong order:

```dockerfile
COPY . .                              # <- your source, changes constantly
RUN pip install --no-cache-dir .      # <- 60 seconds
```

Change one character of Python → the `COPY` layer changes → everything below it is invalidated →
**pip reinstalls every dependency, every time.** Prediction question 1: you expected 2 seconds and
you get 60.

The right order:

```dockerfile
COPY pyproject.toml ./                # <- changes rarely
RUN pip install --no-cache-dir .      # <- 60 seconds, CACHED
COPY src/ ./src/                      # <- changes constantly, but it's last
```

Now a code change invalidates only the final `COPY`. Rebuild: **about a second.**

> 🎯 **Remember this** — **least-changing first, most-changing last.** Dependencies before source
> code. One cache miss invalidates everything below it.

That single principle is most of what separates a 2-second rebuild loop from a 2-minute one, and
you'll feel it on every push in Day 8's CI.

### 🔁 Recall check

<details>
<summary>Your CI rebuilds take 4 minutes even for a one-line README change. The Dockerfile starts <code>COPY . .</code> then <code>RUN pip install -r requirements.txt</code>. Explain and fix.</summary>

`COPY . .` copies **everything**, including the README. Any change to any file invalidates that
layer, and therefore invalidates the `pip install` below it, so dependencies reinstall from scratch
on every push.

```dockerfile
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
```

Add a `.dockerignore` (next section) so `.git`, `.venv`, and caches never enter the build context at
all. The README change now touches no layer that matters, and the build is seconds.
</details>

---

## 4. `.dockerignore`

The **build context** is everything Docker uploads to the daemon before building — by default, your
whole folder. That means `.venv/` (hundreds of MB), `.git/` (your entire history), caches, and
possibly your `.env`.

```
.git
.venv
venv
__pycache__
*.pyc
.pytest_cache
.ruff_cache
*.egg-info
.env
tests/
docs/
*.md
```

Three reasons, in ascending order of importance:

1. **Speed** — a 500 MB context is uploaded on every build.
2. **Cache** — `COPY . .` sees changes in files that have nothing to do with your app.
3. **🚨 Security** — without `.env` listed, a `COPY . .` bakes your secrets into an image layer.
   Layers are permanent and readable: anyone who pulls that image can extract the file, even if a
   later instruction deletes it. Deleting a file in a later layer does **not** remove it from the
   image.

> 🎯 **Remember this** — `.dockerignore` before your first build. `.env` in an image layer is a
> secret you have published, permanently.

---

## 5. Don't run as root

Prediction question 3. By default the process inside a container runs as `root`, and containers are
isolated but not sealed — container escapes exist, and a mounted volume written by root leaves
root-owned files on the host.

The principle is **least privilege**: your API needs to read code and open a socket. It never needs
to install packages or write to `/etc`.

```dockerfile
RUN useradd --create-home --uid 1000 appuser
USER appuser
```

| Token | Meaning |
|---|---|
| `useradd` | Standard Linux user creation, run at build time |
| `--create-home` | Give them a home directory; some tools need one |
| `--uid 1000` | A fixed, non-root id. Predictable for volume permissions |
| `USER appuser` | **Every instruction after this**, and the final `CMD`, runs as that user |

Place `USER` **after** the installs (which need write access to site-packages) and **before**
`CMD`. If you put it too early, `pip install` fails with permission errors.

A useful side effect: as a non-root user the container physically cannot modify its own
dependencies, so a compromised process can't quietly install a package.

---

## 6. Multi-stage builds

Some dependencies need a compiler at install time and nothing at run time. Shipping the compiler
means a bigger image and a wider attack surface. **Multi-stage** builds solve this: build in one
image, copy only the results into a clean one.

```dockerfile
# ---------- stage 1: build ----------
FROM python:3.12-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir --prefix=/install .

# ---------- stage 2: runtime ----------
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /app/src ./src

USER appuser
EXPOSE 8000
CMD ["uvicorn", "insight_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Token | Meaning |
|---|---|
| `AS builder` | Names this stage so a later one can refer to it |
| `--prefix=/install` | Install into a single tidy directory instead of scattering across the system |
| second `FROM` | **Starts over.** A fresh filesystem; stage 1 is discarded |
| `COPY --from=builder` | Copy *out of* the earlier stage — the only thing that survives |
| `gcc`, `libpq-dev` | Build-time only. **Never reach the final image** |
| `libpq5` | The runtime library psycopg2 actually needs |
| `rm -rf /var/lib/apt/lists/*` | Delete apt's package index **in the same `RUN`** |

That last row is a layer subtlety worth internalising. Deleting a file in a *later* `RUN` doesn't
shrink the image, because the earlier layer still contains it. The cleanup has to happen in the same
instruction that created the files, which is why these commands are chained with `&&`.

Result: no compiler in the shipped image, roughly half the size, and a smaller surface for a
scanner to complain about.

> 🎯 **Remember this** — build tools stay in stage 1. The second `FROM` wipes the slate; only
> `COPY --from` survives.

---

## 7. Building and running

```bash
docker build -t insight-api:0.1.0 .
```

| Token | Meaning |
|---|---|
| `build` | Build an image from a Dockerfile |
| `-t insight-api:0.1.0` | **Tag** it `name:version` |
| `.` | The **build context** — this directory. Not "the Dockerfile" |

```bash
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql+psycopg2://student:student123@host.docker.internal:5432/week2_db" \
  insight-api:0.1.0
```

| Token | Meaning |
|---|---|
| `--rm` | Delete the container when it stops. Otherwise they accumulate |
| `-p 8000:8000` | Publish **host port : container port**. This is what `EXPOSE` did not do |
| `-e KEY=value` | Set an environment variable — how Day 4's `Settings` gets configured |
| `host.docker.internal` | From inside a container, this name means "the host machine" |

That hostname deserves a note, because it's the second-most-common container confusion after
`0.0.0.0`. Inside the container, `localhost` is **the container**. Your Postgres is on the *host*.
On Docker Desktop (Windows/Mac) `host.docker.internal` resolves to the host; on Linux, add
`--add-host=host.docker.internal:host-gateway`. The tidier answer is to put both services on one
Docker network with Compose and use the service name — which is exactly what your Module 2
`docker-compose.yml` did when pgAdmin reached Postgres as `postgres`.

Day-to-day commands:

```bash
docker ps                        # running containers
docker ps -a                     # including stopped ones
docker logs <container>          # its stdout/stderr - your uvicorn logs
docker logs -f <container>       # follow, like tail -f
docker exec -it <container> bash # a shell INSIDE a running container
docker images                    # local images and their sizes
docker image prune               # reclaim space from dangling images
docker build --no-cache -t x .   # ignore the cache (to prove a cache theory)
```

`docker exec -it ... bash` is the debugging workhorse: when an image misbehaves, go inside and look.
`ls`, `env`, and `which python` in there answer most questions in seconds.

### Tags: never deploy `latest`

```bash
docker build -t insight-api:latest .          # convenient locally
docker build -t insight-api:$(git rev-parse --short HEAD) .   # what you deploy
```

`latest` is not a magic pointer to the newest build — it's just a default name, and it's **mutable**.
Two problems follow: you can't tell which code is actually running, and you can't roll back to a
specific build. Worse, on Day 8 you'll find that re-pushing the same tag doesn't reliably trigger a
new deployment, because nothing about the requested image changed.

Tag with the **commit SHA**. Then "which version is in production?" has an exact answer that points
at a diff.

> 🎯 **Remember this** — `-p host:container` publishes. `localhost` inside a container is the
> container. **Deploy commit SHAs, never `latest`.**

---

## 8. A health check in the image

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

| Token | Meaning |
|---|---|
| `--interval=30s` | How often to check |
| `--timeout=3s` | A check taking longer than this counts as a failure |
| `--start-period=10s` | Grace period at startup; failures here don't count |
| `--retries=3` | Consecutive failures before the container is marked unhealthy |

Note it uses `python`, not `curl` — a `slim` image has no `curl`, and installing one just to
health-check yourself adds weight for nothing.

This is your Day 4 **liveness** endpoint doing its job: dependency-free, so a database blip doesn't
restart the container. Your Module 2 `docker-compose.yml` used the same mechanism with
`pg_isready` — same idea, different service.

---

## 🔁 Spaced review

<details>
<summary>1. (Day 4) Your container starts, then exits immediately with a Pydantic validation error about <code>database_url</code>. What happened, and is this good or bad?</summary>

`Settings` couldn't build because `DATABASE_URL` wasn't passed with `-e` (or via Compose). Pydantic
validated at startup and refused to run.

This is **good**, and deliberately so. The alternative is a container that starts happily, reports
healthy, accepts traffic, and then throws a `500` on the first request that touches the database.
Fail at startup, loudly, where a deployment can be rolled back automatically.
</details>

<details>
<summary>2. (Day 6) Your Dockerfile runs <code>uvicorn --workers 4</code> and you deploy 3 containers. How many database connections might you open?</summary>

4 workers × 3 containers × (`pool_size` 5 + `max_overflow` 10) = **180 connections**. Postgres
defaults to 100, so most of your containers fail with "too many connections" — and it appears only
under load, once overflow kicks in.

The Day 8 answer: 1 worker per container, scale by adding containers, keep the pool small.
</details>

<details>
<summary>3. (Module 2) Your Compose file has both Postgres and pgAdmin. How does pgAdmin reach Postgres, and what would break if you used <code>localhost</code>?</summary>

By the **service name**, `postgres`. Compose puts both on one network and provides DNS for service
names. `localhost` inside the pgAdmin container means the pgAdmin container itself, where nothing is
listening on 5432, so the connection is refused. Exactly the same confusion as
`host.docker.internal` above.
</details>

---

## 📌 Day 7 on one screen

```dockerfile
FROM python:3.12-slim AS builder     # pin the version. slim, not alpine
WORKDIR /app
COPY pyproject.toml ./               # LEAST-changing first
RUN pip install --no-cache-dir --prefix=/install .
COPY src/ ./src/                     # MOST-changing last

FROM python:3.12-slim                # fresh slate: no compilers ship
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /install /usr/local
COPY --from=builder /app/src ./src
USER appuser                         # after installs, before CMD
EXPOSE 8000                          # documentation ONLY
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]   # exec form; 0.0.0.0
```

| Trap | Fix |
|---|---|
| Slow rebuilds | Dependencies before source |
| Empty reply from container | `--host 0.0.0.0` |
| Port unreachable | `-p 8000:8000`; `EXPOSE` alone does nothing |
| Can't reach host DB | `host.docker.internal`, not `localhost` |
| Secrets in the image | `.dockerignore` with `.env` |
| Killed mid-request | Exec-form `CMD` so `SIGTERM` arrives |
| "Which version is live?" | Tag with the commit SHA |

---

## ➡️ Next

Notebook **[14_docker_practice.ipynb](14_docker_practice.ipynb)** — build the image, measure the
cache-order difference with a stopwatch, break it with `127.0.0.1`, and shrink it with multi-stage.

Day 8 parks the truck in the cloud: **Azure Container Apps**, with a deployment that happens by
itself when you merge.
