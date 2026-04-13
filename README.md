# Data Engineering & LLMs for Organizational Process Automation

Welcome to the complete **Data Engineering & LLMs** curriculum! This is a self-study course designed to take you from beginner to job-ready in data engineering with AI integration.

---

## 📚 Curriculum Overview

This curriculum is organized into **weekly modules**. Each week focuses on a specific set of skills and tools used in real data engineering roles.

### ✅ Completed Weeks

| Week | Topic | Description | Status |
|------|-------|-------------|--------|
| **Week 1** | [Python for Data Engineering](week1-python-for-data/README.md) | Type hints, dataclasses, NumPy, pandas, pathlib, logging, professional Python code | ✅ Ready |
| **Week 2** | [SQL and Relational Databases](week2-sql-databases/README.md) | PostgreSQL, SQL queries, JOINs, GROUP BY, window functions, indexing, DuckDB | ✅ Ready |

### 🚧 Upcoming Weeks

| Week | Topic | Description |
|------|-------|-------------|
| **Week 3** | Data Pipelines & ETL | Building automated data pipelines |
| **Week 4** | Advanced ETL & Orchestration | Apache Airflow, workflow management |
| **Week 5** | Cloud Data Warehouses | Snowflake, BigQuery, cloud platforms |
| **Week 6** | dbt & Data Transformations | dbt for SQL-based data transformations |
| **Module 3** | AI & Vector Databases | pgvector, embeddings, LLM integration |

---

## 🎯 Learning Path

### Week 1: Python for Data Engineering
**Duration:** ~10 hours  
**Prerequisites:** Basic Python knowledge

Learn to write professional, production-ready Python code for data work:
- Type hints and dataclasses for clean code
- NumPy for fast mathematical operations
- pandas for data manipulation and analysis
- pathlib for file system operations
- logging for professional debugging
- Build a complete data pipeline

👉 [Start Week 1](week1-python-for-data/README.md)

### Week 2: SQL and Relational Databases
**Duration:** ~10 hours  
**Prerequisites:** Week 1 (helpful but not required)

Master SQL and relational databases — the foundation of all data engineering:
- Install PostgreSQL with Docker
- Write SQL queries: SELECT, WHERE, ORDER BY, JOINs
- Aggregate data with GROUP BY and HAVING
- Use CTEs and subqueries for complex logic
- Window functions: ROW_NUMBER, RANK, LAG, LEAD
- Understand indexing and query optimization
- Query CSV/Parquet files with DuckDB

👉 [Start Week 2](week2-sql-databases/README.md)

---

## 🚀 How to Use This Curriculum

### 1. Work Through Weeks in Order
Each week builds on the previous one. Start with Week 1 and progress sequentially.

### 2. Follow the Daily Pattern
Each week follows this structure:
- 📖 **Read the theory file** (.md) — concepts explained from zero with analogies
- 💻 **Work through the notebook** (.ipynb) — run queries, see results, practice
- ✏️ **Complete exercises** — test your understanding with challenges

### 3. Set Up Your Environment
Each week includes setup instructions in its README. Generally:
- Install Docker (for databases and tools)
- Create a Python virtual environment
- Install dependencies from `requirements.txt`
- Open VS Code and start learning!

### 4. Don't Rush!
- Master each concept before moving to the next
- Run every code cell yourself
- Complete all exercises
- Take breaks and practice with real datasets

---

## 📁 Project Structure

```
DataEngineeringLLM/
├── week1-python-for-data/          # Week 1 materials
│   ├── README.md                   # Week 1 overview and setup
│   ├── 01_python_for_data.ipynb    # Main notebook (work through this)
│   ├── 01_python_for_data_executed.ipynb  # Reference version
│   ├── data/                       # Sample datasets
│   └── ...
│
├── week2-sql-databases/            # Week 2 materials
│   ├── README.md                   # Week 2 overview and setup
│   ├── DOCKER_GUIDE.md             # Comprehensive Docker explanation
│   ├── day1-setup-and-basics/      # Day 1 lessons
│   ├── day2-joins/                 # Day 2 lessons
│   ├── day3-grouping-and-subqueries/
│   ├── day4-window-functions/
│   ├── day5-indexing-and-duckdb/
│   ├── exercises/                  # Practice exercises
│   └── ...
│
└── README.md                       # This file (curriculum overview)
```

---

## 💡 Learning Philosophy

This curriculum follows these principles:

1. **Explain WHY before HOW** — Every concept starts with why it exists
2. **Start from zero** — No assumptions about prior knowledge
3. **Use analogies** — Abstract concepts paired with real-world examples
4. **Show before/after** — Hard way first, then elegant solution
5. **Progressive complexity** — Simple → complex, one step at a time
6. **Hands-on practice** — Theory files + interactive notebooks + exercises
7. **Production-ready** — Teaches professional practices from day one

---

## 🛠️ Prerequisites

### Software to Install
- **Python 3.10+** — [Download from python.org](https://www.python.org/downloads/)
- **VS Code** — [Download from code.visualstudio.com](https://code.visualstudio.com/)
- **Docker** — [Install guide](https://docs.docker.com/engine/install/)
- **Git** — [Install guide](https://git-scm.com/downloads)

### Skills You Need
- Basic programming knowledge (any language)
- Comfortable using terminal/command prompt
- Willingness to learn!

---

## 🎓 What You'll Be Able to Do After This Curriculum

By the end of all weeks, you'll be able to:

- ✅ Write clean, professional Python code for data work
- ✅ Query and manage relational databases with SQL
- ✅ Build automated ETL/ELT data pipelines
- ✅ Orchestrate workflows with Apache Airflow
- ✅ Work with cloud data warehouses (Snowflake, BigQuery)
- ✅ Transform data with dbt
- ✅ Integrate AI/LLMs into data pipelines
- ✅ Store and query AI embeddings with pgvector

These are the **exact skills** used in data engineering roles at top companies!

---

## 📞 Getting Help

- Check the `README.md` in each week's folder for setup troubleshooting
- For Docker issues, see the comprehensive [DOCKER_GUIDE.md](week2-sql-databases/DOCKER_GUIDE.md)
- Each notebook includes expected output descriptions to verify your results
- Exercises have spoiler solutions for when you get stuck

---

## 📅 Last Updated

**Date:** 2026-04-13  
**Status:** Week 1 ✅ | Week 2 ✅ | More weeks coming!

---

**Ready to start?** Begin with [Week 1: Python for Data Engineering](week1-python-for-data/README.md)!
