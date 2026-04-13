# Week 2: SQL and Relational Databases

Welcome to Week 2 of the **Data Engineering & LLMs for Organizational Process Automation** curriculum! 🎉

In Week 1, you learned Python for data manipulation with pandas, numpy, and Pydantic. This week, you'll master **SQL and relational databases**—the universal language for working with structured data.

## What You'll Learn

- **PostgreSQL**: Install and use the world's most popular open-source relational database
- **SQL Fundamentals**: SELECT, WHERE, ORDER BY, LIMIT—the building blocks of every query
- **JOINs**: Combine data from multiple tables (INNER, LEFT, RIGHT, FULL OUTER, self-joins)
- **Aggregation**: GROUP BY, HAVING, and the power of summarizing data
- **CTEs & Subqueries**: Write complex queries in a readable, step-by-step manner
- **Window Functions**: ROW_NUMBER, RANK, LAG, LEAD, running totals, and the "top-N per group" pattern
- **Indexing**: Understand how databases optimize queries and when to add indexes
- **DuckDB**: Query CSV and Parquet files directly with SQL—no server required

## Why This Matters

The SQL you learn this week is **the same SQL** you'll use throughout your data engineering career:
- In **Week 4**, when building ETL pipelines
- In **Week 6**, with dbt (which generates SQL transformations)
- In **Module 3**, when using pgvector to store AI embeddings
- In every data analyst, data engineer, and ML engineering role you'll ever apply for

SQL hasn't changed much in 40 years because it works. Master it once, use it forever.

## Setup Instructions

> **📘 New to Docker?** Before proceeding, read the comprehensive [DOCKER_GUIDE.md](DOCKER_GUIDE.md). It explains Docker from zero — what containers are, how docker-compose works, essential commands, troubleshooting tips, and best practices. You don't need to be a Docker expert, but understanding the basics will make this week's setup painless.

### Step 1: Install Docker

If you don't have Docker installed, follow the [official Docker installation guide](https://docs.docker.com/engine/install/).

For Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

### Step 2: Start PostgreSQL and pgAdmin

```bash
cd week2-sql-databases
docker compose -f docker/docker-compose.yml up -d
```

This will:
- Start PostgreSQL 16 on port 5432 (database: `week2_db`, user: `student`, password: `student123`)
- Start pgAdmin 4 on port 8080 (email: `student@example.com`, password: `admin`)
- Automatically create our company dataset using `init.sql`

Verify it's running:
```bash
docker ps
```

You should see two containers: `postgres` and `pgadmin`.

### Step 3: Set Up Your Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Open VS Code

Open the `week2-sql-databases` folder as a workspace in VS Code. Install the recommended extensions when prompted:
- Python (ms-python.python)
- Jupyter (ms-toolsai.jupyter)
- SQLTools (mtxr.sqltools)
- SQLTools PostgreSQL Driver (mtxr.sqltools-driver-pg)

## Day-by-Day Learning Path

| Day | Topic | Theory | Practice | Estimated Time |
|-----|-------|--------|----------|----------------|
| **Day 1** | Setup & SQL Basics | What is a database? | First queries: SELECT, WHERE, ORDER BY | ~2 hours |
| **Day 2** | JOINs | How tables relate | INNER, LEFT, RIGHT, FULL, self-joins | ~2 hours |
| **Day 3** | GROUP BY, CTEs, Subqueries | Aggregation patterns | Complex analytical queries | ~2 hours |
| **Day 4** | Window Functions | Beyond GROUP BY | Rankings, running totals, top-N queries | ~2.5 hours |
| **Day 5** | Indexing & DuckDB | Query optimization | EXPLAIN ANALYZE, DuckDB analytics | ~2.5 hours |

**Total: ~10 hours**

## How to Use This Course

Each day follows the same pattern:

1. **Read the theory file** (e.g., `01_theory_what_is_a_database.md`) — This is your patient tutor explaining concepts from zero, with analogies and examples.
2. **Work through the notebook** (e.g., `02_first_queries.ipynb`) — Run each cell, see the results, and complete the "Try It Yourself" exercises.

**Pro tip:** Don't skip the theory files! They explain *why* SQL works the way it does, not just *how*. Understanding the "why" makes everything click.

## Your Dataset

This week you'll work with a realistic company dataset including:
- **departments**: 6 departments across different locations
- **employees**: 50+ employees with salaries, hire dates, managers, and active/inactive status
- **products**: 15+ products in 4 categories (Software, Hardware, Services, Training)
- **sales**: 200+ sales records spanning 12 months with regional data

You'll use this data in PostgreSQL (Days 1-4) and the same data as CSV/Parquet files in DuckDB (Day 5).

## Troubleshooting

**Docker containers won't start:**
```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

**Can't connect to PostgreSQL:**
- Check `docker ps` — is the container running?
- Default port: 5432
- Connection string: `postgresql://student:student123@localhost:5432/week2_db`

**Notebook can't import psycopg2:**
- Make sure your virtual environment is activated: `source .venv/bin/activate`
- Reinstall: `pip install psycopg2-binary`

## Ready? Let's Begin!

Open `day1-setup-and-basics/01_theory_what_is_a_database.md` and start your SQL journey!

## Course Resources

| Resource | Description |
|----------|-------------|
| [DOCKER_GUIDE.md](DOCKER_GUIDE.md) | Comprehensive Docker explanation — images, containers, compose, commands, troubleshooting |
| [README.md](README.md) | This file — course overview and setup instructions |
| `requirements.txt` | Python dependencies for this week |
| `docker/docker-compose.yml` | PostgreSQL + pgAdmin container configuration |
| `docker/init.sql` | Company dataset initialization script |
