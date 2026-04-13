# Docker Explained: A Beginner's Guide

## What is Docker and Why Are We Using It?

### The Problem Docker Solves

Imagine you're building a house. You need electricity, plumbing, internet, and gas. Instead of running wires and pipes directly through your foundation (which would be messy and hard to change), you install them in organized, replaceable modules.

**That's what Docker does for software.**

When you install PostgreSQL directly on your Linux system:
- Configuration files scatter across `/etc/postgresql/`, `/var/lib/postgresql/`, `/var/log/postgresql/`
- It might conflict with other software using the same ports
- Different projects might need different PostgreSQL versions
- Uninstalling is tedious and often leaves remnants
- Your colleague's machine might behave differently

**With Docker, PostgreSQL runs in its own isolated container** — like a lightweight virtual machine that contains everything it needs:

```
Your Linux System
├── Docker Engine
│   ├── PostgreSQL Container (port 5432, version 16)
│   ├── pgAdmin Container (port 8080)
│   └── [Any other container, isolated from each other]
└── Your Files
```

Each container is self-contained. When you're done, `docker compose down` removes everything cleanly. No traces, no conflicts.

---

## Key Docker Concepts (Explained Simply)

### 1. Image = Recipe

A **Docker image** is a read-only template that describes what a container should contain. It's like a recipe or a blueprint.

```
postgres:16  →  "Download PostgreSQL 16, configure it, make it ready"
ubuntu:22.04 →  "Download Ubuntu 22.04, set up the base system"
python:3.11  →  "Download Python 3.11 with pip and common tools"
```

You don't create images from scratch — you pull them from **Docker Hub** (hub.docker.com), which is like GitHub but for Docker images.

### 2. Container = Running Instance

A **container** is a running copy of an image. Think of it like this:

| Term | Analogy | Software Equivalent |
|---|---|---|
| **Image** | A recipe for chocolate cake | The blueprint |
| **Container** | The actual cake you bake from the recipe | The running program |

You can run multiple containers from the same image:

```
postgres:16 image  →  Container A (project 1, port 5432)
postgres:16 image  →  Container B (project 2, port 5433)
```

They're isolated from each other — what happens in Container A doesn't affect Container B.

### 3. Dockerfile = Custom Recipe

A **Dockerfile** is a text file with step-by-step instructions to build a custom image. For example:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

This says: "Start with Python 3.11, copy my code, install dependencies, and run app.py."

### 4. Docker Compose = Multi-Container Orchestrator

**Docker Compose** lets you define multiple containers and how they connect using a simple YAML file. Instead of running multiple `docker run` commands, you write one file:

```yaml
services:
  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: week2_db
      POSTGRES_USER: student
      POSTGRES_PASSWORD: student123
  
  pgadmin:
    image: dpage/pgadmin4
    ports:
      - "8080:80"
```

Then one command starts everything:

```bash
docker compose up -d
```

---

## Understanding docker-compose.yml

Let's break down the file in `docker/docker-compose.yml` line by line.

### The Full File

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16
    container_name: week2_postgres
    environment:
      POSTGRES_DB: week2_db
      POSTGRES_USER: student
      POSTGRES_PASSWORD: student123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U student -d week2_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4
    container_name: week2_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: student@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: "False"
    ports:
      - "8080:80"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

### Line-by-Line Explanation

#### `version: "3.8"`
Specifies the Docker Compose file format. Version 3.8 is widely compatible.

#### `services:`
This section defines each container you want to run. Each service becomes one container.

#### `postgres:` (Service Name)
The first container. We call it `postgres` (you can name it anything).

#### `image: postgres:16`
Pulls the official PostgreSQL version 16 image from Docker Hub. The format is `name:tag`.

#### `container_name: week2_postgres`
Gives the container a readable name. Without this, Docker generates random names like `angry_feynman`.

#### `environment:`
Sets environment variables **inside** the container. PostgreSQL reads these on first startup:
- `POSTGRES_DB: week2_db` → Creates a database named `week2_db`
- `POSTGRES_USER: student` → Creates a user named `student`
- `POSTGRES_PASSWORD: student123` → Sets the password

#### `ports: - "5432:5432"`
Maps ports between your machine and the container. The format is `"host:container"`:

```
"5432:5432" means:
  Your machine's port 5432  ←→  Container's port 5432
```

So when your Python script connects to `localhost:5432`, it actually reaches PostgreSQL inside the container.

**What if port 5432 is already used on your machine?** Change the host port:

```yaml
ports:
  - "5433:5432"  # Your machine uses 5433, container still uses 5432
```

Then connect to `localhost:5433` instead.

#### `volumes:`
Persistent storage. Containers are **ephemeral** — when you delete a container, everything inside disappears. Volumes preserve data.

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
  - ./init.sql:/docker-entrypoint-initdb.d/init.sql
```

**Named volume** (`postgres_data:/var/lib/postgresql/data`):
- `postgres_data` is a Docker-managed volume (stored in `/var/lib/docker/volumes/`)
- `/var/lib/postgresql/data` is where PostgreSQL stores its data inside the container
- Even if you delete the container, your database files survive in the volume

**Bind mount** (`./init.sql:/docker-entrypoint-initdb.d/init.sql`):
- `./init.sql` is a file on your actual machine (in the `docker/` folder)
- `/docker-entrypoint-initdb.d/init.sql` is the path inside the container
- PostgreSQL automatically runs any `.sql` files in `/docker-entrypoint-initdb.d/` on first startup
- This is how our company dataset gets created automatically!

#### `healthcheck:`
Docker periodically checks if PostgreSQL is actually running and responsive:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U student -d week2_db"]
  interval: 10s    # Check every 10 seconds
  timeout: 5s      # If no response in 5s, consider it failed
  retries: 5       # After 5 failures, mark container as unhealthy
```

`pg_isready` is a PostgreSQL utility that tests if the server is accepting connections.

#### `pgadmin:` (Second Service)
A web-based interface for managing PostgreSQL visually.

#### `depends_on: - postgres`
Ensures PostgreSQL starts **before** pgAdmin. pgAdmin needs PostgreSQL to be available.

---

## Essential Docker Commands

### Starting and Stopping

```bash
# Start all containers in the background (detached mode)
docker compose -f docker/docker-compose.yml up -d

# Start and see logs in real-time (foreground)
docker compose -f docker/docker-compose.yml up

# Stop all containers (preserves data in volumes)
docker compose -f docker/docker-compose.yml down

# Stop AND delete volumes (destroys all database data!)
docker compose -f docker/docker-compose.yml down -v
```

### Checking Status

```bash
# List running containers
docker ps

# Should show something like:
# CONTAINER ID   IMAGE            STATUS          PORTS                    NAMES
# abc123         postgres:16      Up 2 minutes    0.0.0.0:5432->5432/tcp   week2_postgres
# def456         dpage/pgadmin4   Up 2 minutes    0.0.0.0:8080->80/tcp     week2_pgadmin

# Check container health
docker inspect --format='{{.State.Health.Status}}' week2_postgres
# Output: healthy (or starting, or unhealthy)

# View logs from a specific container
docker logs week2_postgres

# Follow logs in real-time (like tail -f)
docker logs -f week2_postgres
```

### Executing Commands Inside Containers

```bash
# Open a PostgreSQL shell inside the container
docker exec -it week2_postgres psql -U student -d week2_db

# Now you're inside PostgreSQL! You can run SQL directly:
# week2_db=# SELECT * FROM company.employees LIMIT 5;

# Exit PostgreSQL with \q

# Open a general shell inside the container
docker exec -it week2_postgres bash
# Now you're in a Linux shell inside the container
# ls /var/lib/postgresql/data
# exit
```

### Managing Images and Volumes

```bash
# List all downloaded images
docker images

# Remove an image
docker rmi postgres:16

# List all volumes
docker volume ls

# Remove a specific volume
docker volume rm week2-sql-databases_postgres_data

# Clean up everything unused (images, volumes, networks)
docker system prune -a --volumes
# ⚠️ WARNING: This deletes all unused data. Be careful!
```

---

## Troubleshooting Docker

### Problem: "Port 5432 is already in use"

**Cause:** Another PostgreSQL instance (or another service) is already using port 5432.

**Solution:** Change the host port in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"  # Use 5433 on your machine instead
```

Then connect to `localhost:5433` in your Python scripts.

### Problem: Container won't start

**Check logs:**
```bash
docker logs week2_postgres
```

Look for error messages. Common issues:
- Corrupted data volume
- Missing permissions
- Conflicting environment variables

**Reset solution:**
```bash
# Stop containers
docker compose -f docker/docker-compose.yml down

# Delete the data volume (⚠️ destroys database data!)
docker volume rm week2-sql-databases_postgres_data

# Start fresh
docker compose -f docker/docker-compose.yml up -d
```

### Problem: `init.sql` didn't run

**Cause:** PostgreSQL only runs init scripts on **first startup** (when the data directory is empty). If you've already started PostgreSQL before, the data volume exists and init scripts are skipped.

**Solution:**
```bash
# Stop and delete the volume
docker compose -f docker/docker-compose.yml down -v

# Start fresh (init.sql will run)
docker compose -f docker/docker-compose.yml up -d

# Wait 10-15 seconds for initialization
docker logs -f week2_postgres
# Wait until you see "database system is ready to accept connections"
```

### Problem: Can't connect from Python

**Checklist:**
1. Is the container running? → `docker ps`
2. Is the port correct? → Should be `localhost:5432` (or `5433` if you changed it)
3. Are credentials correct? → user: `student`, password: `student123`, dbname: `week2_db`
4. Is PostgreSQL healthy? → `docker inspect --format='{{.State.Health.Status}}' week2_postgres`

**Test connection:**
```bash
docker exec -it week2_postgres psql -U student -d week2_db -c "SELECT 1;"
```

If this works, the database is fine. The issue is in your Python connection string.

---

## Docker Best Practices

### 1. Always Use `-d` (Detached Mode)

```bash
docker compose up -d  # Runs in background
```

Without `-d`, the containers run in your terminal. If you close the terminal or press Ctrl+C, the containers stop.

### 2. Name Your Containers

```yaml
container_name: week2_postgres  # Easy to reference
```

Without this, Docker generates random names like `fervent_darwin` or `angry_babbage`.

### 3. Use `.dockerignore` (Like `.gitignore` for Docker)

When building custom images, create a `.dockerignore` file to exclude unnecessary files (like `.venv`, `__pycache__`, `.git`).

### 4. Don't Store Sensitive Data in docker-compose.yml (In Production)

For this course, passwords in the YAML file are fine. In production, use:
- `.env` files
- Docker secrets
- Environment variable managers

### 5. Health Checks Are Your Friend

The `healthcheck` section in our compose file lets you know when PostgreSQL is actually ready, not just when the container started.

---

## Forward Connection

> **Looking ahead:** Docker isn't just for this course. In **Week 4**, you'll use Docker to run Apache Airflow for ETL pipeline orchestration. In **Week 6**, you'll containerize dbt projects. In **Module 3**, you'll run vector databases in Docker for AI embeddings. Understanding Docker now makes every future module easier.

---

## Quick Reference Card

| Command | What it does |
|---------|-------------|
| `docker compose up -d` | Start all containers in background |
| `docker compose down` | Stop containers (keep data) |
| `docker compose down -v` | Stop containers AND delete data volumes |
| `docker ps` | List running containers |
| `docker logs <name>` | View container logs |
| `docker exec -it <name> bash` | Open shell inside container |
| `docker compose up -d --build` | Rebuild images and restart |
| `docker images` | List downloaded images |
| `docker volume ls` | List all volumes |

---

## Docker in One Picture

```
docker-compose.yml
       │
       ▼
┌─────────────────────────────────────────────┐
│              Docker Engine                  │
│                                             │
│  ┌──────────────────┐  ┌─────────────────┐  │
│  │  week2_postgres  │  │  week2_pgadmin  │  │
│  │  (PostgreSQL 16) │  │  (Web UI)       │  │
│  │                  │  │                 │  │
│  │  Port: 5432      │  │  Port: 80       │  │
│  │  User: student   │  │  Email: student │  │
│  │  DB: week2_db    │  │  @example.com   │  │
│  │                  │  │                 │  │
│  │  ┌────────────┐  │  └─────────────────┘  │
│  │  │  Volume:   │  │         ▲              │
│  │  │  Data      │  │         │              │
│  │  │  Persists  │  │    Depends on         │
│  │  └────────────┘  │    postgres           │
│  └──────────────────┘                       │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Init Script (runs once on start)   │    │
│  │  → Creates company schema           │    │
│  │  → Creates 4 tables                 │    │
│  │  → Inserts 50+ employees            │    │
│  │  → Inserts 200+ sales               │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
       │                           │
       ▼                           ▼
  localhost:5432            localhost:8080
  (Python connects)         (Browser opens pgAdmin)
```

Now you understand Docker! Return to the [README](../README.md) to continue with the course setup.
