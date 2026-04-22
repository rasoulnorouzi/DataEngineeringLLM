# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**DataEngineeringLLM** is a comprehensive, self-paced curriculum for learning data engineering and AI integration. The course is structured as **weekly modules**, each combining:
- Theory documents explaining concepts from zero
- Jupyter notebooks with working examples and exercises
- Sample datasets to practice with
- Supporting tools (Docker for databases, Python libraries for data processing)

**Current Status:**
- ✅ Week 1: Python for Data Engineering (complete)
- ✅ Week 2: SQL and Relational Databases (complete)
- 🚧 Week 3-6+ in development

This is primarily an **educational content repository**, not a production application. The "code" here consists of tutorial notebooks, theory documents, and sample data. Your role is to help maintain, expand, and improve the curriculum materials.

---

## Repository Structure

```
DataEngineeringLLM/
├── week1-python-for-data/          # Week 1: Python fundamentals
│   ├── 01_python_for_data.ipynb              # Main learning notebook (blank version)
│   ├── 01_python_for_data_executed.ipynb    # Reference with all outputs
│   ├── data/                                 # Sample datasets (barbie.csv, etc)
│   ├── data_output/                          # Output from student exercises
│   ├── .vscode/settings.json                 # Jupyter kernel settings
│   └── README.md                             # Week 1 setup and learning guide
│
├── week2-sql-databases/            # Week 2: SQL & relational databases
│   ├── docker/
│   │   ├── docker-compose.yml               # PostgreSQL + pgAdmin setup
│   │   └── init.sql                         # Database schema & sample data
│   ├── day1-setup-and-basics/               # Day 1 theory and practice
│   ├── day2-joins/                          # Day 2 lessons
│   ├── day3-grouping-and-subqueries/
│   ├── day4-window-functions/
│   ├── day5-indexing-and-duckdb/
│   ├── exercises/                           # Practice exercises
│   ├── data/                                # Sample CSV/data files
│   ├── .vscode/settings.json
│   ├── requirements.txt
│   ├── DOCKER_GUIDE.md                      # Comprehensive Docker explanation
│   └── README.md                            # Week 2 setup guide
│
└── README.md                        # Curriculum overview & learning path
```

---

## Common Tasks & Commands

### Setting Up a Week's Environment

Each week is independent with its own Python environment:

```bash
# Navigate to the week folder
cd week1-python-for-data    # or week2-sql-databases

# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate      # Linux/Mac
# or
.venv\Scripts\activate         # Windows

# Install dependencies (Week 1 has no requirements.txt, install manually)
# Week 1:
pip install jupyter pandas numpy pyarrow pathlib logging

# Week 2:
pip install -r requirements.txt
```

### Running Jupyter Notebooks

```bash
# From the week directory with .venv activated:
jupyter notebook

# Opens a browser window. Click on the .ipynb file to open it.
# The blank version (01_python_for_data.ipynb) is for students to fill in.
# The _executed version is a reference with all outputs shown.
```

### Week 2: Starting Docker Services

Week 2 uses PostgreSQL in Docker for database exercises:

```bash
cd week2-sql-databases

# Start PostgreSQL and pgAdmin
docker compose -f docker/docker-compose.yml up -d

# Verify containers are running
docker ps

# Stop services
docker compose -f docker/docker-compose.yml down

# View logs
docker compose -f docker/docker-compose.yml logs postgres
```

**Access points:**
- **pgAdmin** (web UI): http://localhost:8080
  - Email: `student@example.com`, Password: `admin`
- **PostgreSQL** (command line or apps)
  - Host: `localhost`, Port: `5432`
  - Database: `week2_db`, User: `student`, Password: `student123`

---

## Key Design Principles

### 1. Curriculum Structure
- **Theory First**: Each day starts with a theory document explaining *why* concepts exist, not just *how* to use them
- **Learning by Doing**: Jupyter notebooks guide students through hands-on examples before asking them to solve problems independently
- **Progressive Complexity**: Concepts build from simple to complex over each week
- **Beginner-Friendly Language**: Assumes no prior knowledge; uses analogies and real-world examples

### 2. Notebook Pattern (Week 1)
- Blank notebook (`01_python_for_data.ipynb`): Students work through this
- Executed notebook (`01_python_for_data_executed.ipynb`): Reference version with all outputs visible
- Both notebooks follow this structure:
  - Concept explanation + analogy
  - Working code example
  - "Try It Yourself" exercise
  - Solution revealed (collapsible)

### 3. Week 2 Organization (Day-by-Day)
- Each day folder contains:
  - `01_theory_*.md` — Conceptual explanation
  - `02_*.ipynb` — Hands-on notebook with practice
  - Example SQL queries and expected outputs
- Exercises folder has additional practice problems with solutions

### 4. Data Handling
- Sample datasets stored in `data/` folders
- Output from student work typically goes to `data_output/` or `output/` directories
- CSVs and Parquet files used for teaching
- Week 2's `init.sql` creates a company dataset with tables like `employees`, `departments`, `sales`

---

## Common Content Types You'll Work With

### Jupyter Notebooks (.ipynb)
- **Primary learning format** for this curriculum
- Contains Markdown (theory), code (examples + exercises), and outputs
- Best edited in Jupyter or VS Code with the Jupyter extension
- Two versions per notebook:
  - **Blank**: for students to fill in (intended for interactive use)
  - **Executed**: reference version with all outputs (read-only reference)

### Theory Documents (.md)
- Explain concepts from first principles
- Include analogies, "bad way vs good way" comparisons
- Always explain *why* before showing *how*
- Used by students before opening related notebooks

### Sample Datasets
- CSV files in `data/` folders
- Realistic but small enough for quick operations
- Week 1 uses `barbie.csv` (movie data); Week 2 uses `init.sql` to seed PostgreSQL
- These should be treated as immutable fixtures for reproducibility

---

## When Editing Curriculum Materials

### Adding Exercises
- Include 2-3 difficulty levels when possible
- Provide collapsible solutions so students can check themselves
- Test the solution in a running notebook before adding it

### Updating Theory Documents
- Maintain the "explain why first" principle
- Use analogies and comparisons to concrete scenarios
- Include examples before asking students to apply concepts
- Keep language beginner-friendly (avoid jargon without explaining)

### Fixing Notebook Issues
- Always test in a fresh Jupyter kernel to ensure reproducibility
- Clear all outputs from the working notebook before committing
- Keep the executed version updated as reference
- Note expected outputs in comments if they might surprise students

### Adding New Weeks
- Follow the same structure: theory + notebook + exercises + data
- Create a README.md with setup instructions and learning objectives
- Include a day-by-day breakdown and estimated time commitment
- Add to the curriculum overview in the main README.md

---

## Environment Details

- **Python**: 3.10+ (currently tested on 3.13.5)
- **Virtual Environment**: `venv` (one per week to avoid conflicts)
- **Key Libraries**:
  - **Week 1**: jupyter, pandas, numpy, pyarrow, pathlib (built-in), logging (built-in)
  - **Week 2**: jupyter, pandas, sqlalchemy, psycopg2-binary, duckdb, python-dotenv, tabulate
- **Database**: PostgreSQL 16 (via Docker in Week 2)
- **Interactive Environment**: Jupyter Notebook or VS Code with Jupyter extension

---

## Testing & Verification

- **Notebooks**: Run all cells interactively to verify outputs
- **Docker Services**: Use `docker ps` and `docker compose logs` to verify health
- **SQL Queries**: Execute in pgAdmin or psql to verify expected results
- **No automated testing**: This is a curriculum, not a production codebase; verification is manual and interactive

---

## Git & Version Control

- Main branch contains stable, tested curriculum materials
- Sample notebooks are tracked with outputs cleared (except `_executed` versions)
- Docker volumes (database data) are in `.gitignore`
- Virtual environments are in `.gitignore`
- Commit messages should reference the week and topic being added or fixed (e.g., "Week 1: Add dataclasses exercise")

---

## Notes for Claude Code

- This repo prioritizes **educational clarity** over code elegance
- "Simplify" and "refactor" requests should improve **learning outcomes**, not just code style
- When explaining code or concepts, **use the same analogies** present in the materials (consistency matters for students)
- When extending curriculum, follow the **existing patterns** for structure and pedagogy
- The "audience" is learners with **beginner to intermediate experience**; avoid advanced shortcuts
