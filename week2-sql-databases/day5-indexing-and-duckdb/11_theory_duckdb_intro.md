# What Is DuckDB? — An Introduction to Embedded Analytics

> "SQLite for analytics." No server. No Docker. No configuration. Just `import duckdb` and start querying.

---

## Table of Contents

1. [What Is DuckDB?](#1-what-is-duckdb)
2. [Why Does DuckDB Exist?](#2-why-does-duckdb-exist)
3. [Columnar vs Row Storage](#3-columnar-vs-row-storage)
4. [The Connection to Parquet](#4-the-connection-to-parquet)
5. [When to Use DuckDB vs PostgreSQL](#5-when-to-use-duckdb-vs-postgresql)

---

## 1. What Is DuckDB?

DuckDB is an **in-process analytical database management system (DBMS)**. It runs *inside* your Python process — there is no separate server to install, no Docker container to manage, and no configuration files to set up. You install it with `pip install duckdb`, import it like any other library, and start running SQL queries immediately.

```python
import duckdb

# That's it — no connection string, no server, no setup
result = duckdb.sql("SELECT 1 AS value")
print(result)
# ┌───────┐
# │ value │
# │ int32 │
# ├───────┤
# │     1 │
# └───────┘
```

The key idea: **DuckDB is embedded**. Just like SQLite embeds a SQL engine into your application, DuckDB embeds an *analytical* SQL engine into your Python process. The entire database engine lives in a single library import.

### DuckDB at a Glance

| Feature | Description |
|---|---|
| **Installation** | `pip install duckdb` — that's all |
| **Server required?** | No — runs inside your process |
| **Configuration** | Zero — works out of the box |
| **Primary workload** | Analytical queries (OLAP) |
| **Storage model** | Columnar |
| **Concurrency** | Single-writer, single-reader (not for multi-user apps) |
| **Best for** | Data exploration, analytics, prototyping |

---

## 2. Why Does DuckDB Exist?

PostgreSQL is powerful — you have seen that in this week's labs. But PostgreSQL is a **server** that you must install, configure, start, and maintain. You need:

- A running PostgreSQL service (or Docker container)
- Connection strings with host, port, username, password
- Database and table creation before loading data
- Ongoing server management

For **quick data exploration on local files** — CSVs, Parquet, JSON files sitting on your laptop — this overhead is unnecessary.

### The Problem DuckDB Solves

Imagine you have a CSV file and want to run a quick aggregation:

**With PostgreSQL**, you would:
1. Start the PostgreSQL server
2. Create a database
3. Create a table with the right schema
4. Copy the CSV data into the table
5. Run your query
6. Clean up

**With DuckDB**, you would:
```python
import duckdb

result = duckdb.sql("""
    SELECT department, AVG(salary) AS avg_salary
    FROM read_csv_auto('employees.csv')
    GROUP BY department
    ORDER BY avg_salary DESC
""")
print(result)
```

That is it. No server. No setup. DuckDB reads the CSV directly, infers the schema, and returns results.

### Analytical vs Transactional Workloads

DuckDB is designed for **analytical queries** (OLAP — Online Analytical Processing), not transactional workloads (OLTP — Online Transaction Processing).

| Aspect | OLAP (DuckDB) | OLTP (PostgreSQL) |
|---|---|---|
| **Typical query** | `SELECT department, AVG(salary), COUNT(*) FROM employees GROUP BY department` | `INSERT INTO orders (customer_id, product_id, quantity) VALUES (42, 7, 1)` |
| **Query pattern** | Few queries, each scanning millions of rows | Many queries, each touching few rows |
| **Goal** | Compute aggregates, find patterns, explore data | Insert/update/delete individual records reliably |
| **Window functions** | Heavy use | Available but less central |
| **Full table scans** | Common and optimized | Generally avoided |

DuckDB excels at `GROUP BY`, window functions, large aggregations, and full-table analytical scans. It is **not** designed for hundreds of small `INSERT` statements per second — that is PostgreSQL's domain.

---

## 3. Columnar vs Row Storage

This is the single most important concept for understanding why DuckDB is fast at analytics.

### Row-Based Storage (PostgreSQL, most databases)

Data is stored **row by row**. All columns of a single record are stored together sequentially on disk.

```
Row 1: | Alice  | Engineering | 75000 | 2019-03-15 |
Row 2: | Bob    | Marketing   | 62000 | 2020-07-01 |
Row 3: | Carol  | Engineering | 81000 | 2018-11-20 |
Row 4: | Dave   | Marketing   | 58000 | 2021-02-14 |
```

**Good for:** Fetching complete records. When you run `SELECT * FROM employees WHERE name = 'Alice'`, the database reads one contiguous block and gets all columns at once.

### Columnar Storage (DuckDB, Parquet)

Data is stored **column by column**. All values of a single column are stored together sequentially.

```
Column 'name':        | Alice | Bob  | Carol | Dave  |
Column 'department':  | Engineering | Marketing | Engineering | Marketing |
Column 'salary':      | 75000 | 62000 | 81000 | 58000 |
Column 'hire_date':   | 2019-03-15 | 2020-07-01 | 2018-11-20 | 2021-02-14 |
```

**Good for:** Analyzing specific columns. When you run `SELECT AVG(salary) FROM employees`, DuckDB **only reads the salary column** — it completely skips name, department, and hire_date.

### Why This Matters for Analytics

Consider the query:

```sql
SELECT department, AVG(salary)
FROM employees
GROUP BY department;
```

| Storage Type | What Gets Read |
|---|---|
| **Row-based** (PostgreSQL) | All columns for every row — even though the query only uses `department` and `salary` |
| **Columnar** (DuckDB) | Only the `department` and `salary` columns — all other columns are never read from disk |

For a table with 20 columns and 10 million rows, if your query only uses 3 columns, a columnar engine reads **85% less data**. This is the primary reason DuckDB is fast for analytical workloads.

### Visual Comparison

```
Query: SELECT AVG(salary) FROM employees;

ROW STORAGE:                    COLUMNAR STORAGE:
Read entire rows:               Read only salary column:
┌────────────────────┐          ┌──────────────────┐
│ name: Alice        │          │ 75000            │
│ dept: Engineering  │  SKIP   │ 62000            │
│ salary: 75000      │ ──────►  │ 81000            │
│ date: 2019-03-15   │          │ 58000            │
├────────────────────┤          │ ...              │
│ name: Bob          │          └──────────────────┘
│ dept: Marketing    │  SKIP
│ salary: 62000      │ ──────►  Only these values are read
│ date: 2020-07-01   │          from disk — huge I/O savings
├────────────────────┤
│ name: Carol        │
│ dept: Engineering  │  SKIP
│ salary: 81000      │ ──────►
│ date: 2018-11-20   │
└────────────────────┘
```

---

## 4. The Connection to Parquet

Parquet is a **columnar file format** — the same storage philosophy that DuckDB uses internally. This creates a powerful synergy.

### What Is Parquet?

Parquet is a binary columnar storage format designed for efficient data storage and retrieval. It stores data column-by-column on disk, with built-in compression and statistics (min/max values, null counts) that help query engines skip irrelevant data.

### Why DuckDB + Parquet Is So Efficient

When DuckDB reads a Parquet file, it is essentially a **column-to-column pipeline**:

```
Parquet file on disk          DuckDB in memory
┌──────────────────┐          ┌──────────────────┐
│ Column: id       │ ───────► │ Column: id       │
│ Column: name     │          │ Column: name     │
│ Column: amount   │ ───────► │ Column: amount   │
│ Column: date     │          │ Column: date     │
└──────────────────┘          └──────────────────┘

     Columnar                       Columnar
     storage                        processing

No format conversion needed — data flows directly from disk to memory.
```

When your query only needs certain columns, DuckDB reads **only those columns from the Parquet file**, skipping the rest entirely. Combined with Parquet's built-in compression, this means DuckDB can analyze gigabytes of data in seconds.

### Connecting to Week 1

In Week 1, you wrote Parquet files with pandas:

```python
import pandas as pd

df = pd.read_csv('sales_data.csv')
df.to_parquet('sales_data.parquet')  # You did this in Week 1
```

Now, with DuckDB, you can **query those same Parquet files using SQL** — no need to load them back into pandas:

```python
import duckdb

result = duckdb.sql("""
    SELECT
        product_category,
        SUM(revenue) AS total_revenue,
        AVG(quantity) AS avg_quantity,
        COUNT(*) AS num_transactions
    FROM 'sales_data.parquet'
    GROUP BY product_category
    ORDER BY total_revenue DESC
""")
result.show()
```

DuckDB reads the Parquet file directly — no pandas overhead, no data loading into an intermediate format. The Parquet columns flow straight into DuckDB's columnar query engine.

### DuckDB's Parquet Advantages

| Capability | Example |
|---|---|
| **Direct Parquet query** | `SELECT * FROM 'data.parquet'` |
| **Glob patterns** | `SELECT * FROM 'data/*.parquet'` — query multiple files at once |
| **Column pruning** | Only reads columns referenced in your query |
| **Predicate pushdown** | Filters are applied while reading, reducing data loaded |
| **Mixed sources** | `SELECT * FROM 'orders.parquet' o JOIN 'customers.parquet' c ON o.customer_id = c.id` |

---

## 5. When to Use DuckDB vs PostgreSQL

DuckDB and PostgreSQL are not competitors — they solve different problems. Choosing the right tool depends on your workload.

### Quick Decision Guide

| Scenario | Use DuckDB | Use PostgreSQL |
|---|:---:|:---:|
| Exploring a CSV or Parquet file on your laptop | Yes | Overkill |
| Running `GROUP BY` aggregations on millions of rows | Yes | Works, but more setup |
| Building a production web application backend | No | Yes |
| Prototyping a data transformation before deploying to production | Yes | Possible, but slower iteration |
| Storing user accounts, sessions, or application state | No | Yes |
| Multi-user concurrent access to the same database | No | Yes |
| Single-user analytical script or Jupyter notebook | Yes | Overkill |
| Processing a batch of files and writing results | Yes | Unnecessary complexity |
| Storing data that must persist beyond your script | Possible, but... | Yes — designed for this |
| Running window functions over large datasets | Yes | Works, but setup overhead |

### DuckDB: The Local Analytics Tool

Use DuckDB when your work involves:

- **Local data exploration** — Quickly understanding what is inside CSV, Parquet, or JSON files
- **Prototyping** — Testing SQL queries and transformations before deploying them elsewhere
- **Single-user scripts** — Data pipelines that run on your machine, not shared across a team
- **Batch processing** — Reading files, transforming them, and writing results
- **Ad-hoc analysis** — Answering one-off business questions with SQL on local files

```python
# Typical DuckDB workflow — everything in one script
import duckdb

# Read from multiple file types
csv_data = duckdb.sql("SELECT * FROM read_csv_auto('raw_data.csv')")
parquet_data = duckdb.sql("SELECT * FROM 'enriched_data.parquet'")

# Transform and analyze
result = duckdb.sql("""
    WITH combined AS (
        SELECT *, 'csv' AS source FROM csv_data
        UNION ALL
        SELECT *, 'parquet' AS source FROM parquet_data
    )
    SELECT
        date_trunc('month', order_date) AS month,
        source,
        COUNT(*) AS orders,
        SUM(amount) AS revenue
    FROM combined
    GROUP BY ALL
    ORDER BY month, source
""")

# Write results
result.write_parquet('monthly_summary.parquet')
```

### PostgreSQL: The Production Database

Use PostgreSQL when your work involves:

- **Production applications** — Web backends, APIs, services that must run 24/7
- **Multi-user access** — Multiple people or services reading and writing simultaneously
- **Transactional workloads** — Many small INSERT, UPDATE, DELETE operations
- **Data integrity** — Foreign keys, constraints, ACID transactions across multiple tables
- **Long-term storage** — Data that must persist reliably beyond individual scripts or sessions

### The Typical Data Engineering Workflow

In practice, data engineers often use **both**:

```
┌─────────────────────────────────────────────────────────────┐
│                     Development Phase                       │
│                                                             │
│   DuckDB (local)                                            │
│   ├── Explore raw CSV/Parquet files                         │
│   ├── Prototype SQL transformations                         │
│   ├── Validate logic and results                            │
│   └── Iterate quickly without server overhead               │
│                                                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Production Phase                        │
│                                                             │
│   PostgreSQL / Cloud Data Warehouse                         │
│   ├── Deploy proven transformations as dbt models           │
│   ├── Schedule recurring data pipelines                     │
│   ├── Serve BI dashboards and downstream consumers          │
│   └── Ensure data quality with tests and constraints        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Forward Connection:** In Module 4, you will use DuckDB to prototype transformations locally before deploying them as dbt models in your production data warehouse. The SQL you write and test in DuckDB will be nearly identical to the SQL that runs in your production environment — DuckDB is your local sandbox for production-grade data engineering.

---

## Summary

| Concept | Key Takeaway |
|---|---|
| **Embedded database** | DuckDB runs inside your Python process — no server, no Docker, no config |
| **Purpose-built for analytics** | Optimized for `GROUP BY`, aggregations, window functions, full-table scans |
| **Columnar storage** | Reads only the columns your query needs — massive I/O savings for analytics |
| **Parquet synergy** | Column-to-column data flow makes DuckDB + Parquet extremely efficient |
| **Local-first tool** | Perfect for exploration, prototyping, and single-user analytical scripts |
| **Not a PostgreSQL replacement** | Use PostgreSQL for production apps, multi-user access, and transactional workloads |

DuckDB gives you the power of SQL analytics with the simplicity of a Python library. It is the fastest way to go from "I have a data file" to "I have answers from my data."
