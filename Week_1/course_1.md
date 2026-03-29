# Week 1 — Python for Data (Full Course)

> **Goal:** Write clean, professional Python before touching any data engineering tool.
> **Time commitment:** ~10 hours across 5 days
> **Prerequisites:** Basic programming knowledge (variables, loops, functions in any language)

---

## Day 1: Environment Setup + Core Python Patterns (~2 hours)

### 1.1 — Why Environment Management Matters

In data engineering, you'll work on multiple projects simultaneously. Project A might need Python 3.11 with pandas 1.5, while Project B needs Python 3.12 with pandas 2.2. Without proper environment management, these projects will break each other. Two tools solve this:

- **pyenv** — manages multiple Python *versions* on your machine
- **venv** — creates isolated *environments* per project (separate installed packages)

### 1.2 — Installing pyenv

```bash
# macOS (using Homebrew)
brew update
brew install pyenv

# Linux (using the installer script)
curl https://pyenv.run | bash

# After install, add these to your ~/.bashrc or ~/.zshrc:
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Restart your shell, then:
pyenv install 3.12.4
pyenv global 3.12.4       # sets the default Python version system-wide
python --version           # should show Python 3.12.4
```

**On Windows**, use [pyenv-win](https://github.com/pyenv-win/pyenv-win) or simply install Python 3.12+ from python.org. The concepts are identical.

### 1.3 — Creating a Virtual Environment

```bash
# Navigate to your project folder
mkdir ~/week1-project && cd ~/week1-project

# Create a virtual environment (a folder called .venv with its own Python)
python -m venv .venv

# Activate it
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Your prompt changes to show (.venv)
# Now install packages — they go into .venv/, not your system Python
pip install pandas numpy pydantic pyarrow python-dotenv

# Save your dependencies
pip freeze > requirements.txt

# Later, anyone can reproduce your environment:
# pip install -r requirements.txt

# Deactivate when done
deactivate
```

**Rule of thumb:** Never `pip install` anything without an active virtual environment. If you don't see `(.venv)` in your prompt, stop and activate first.

### 1.4 — Type Hints

Type hints don't change how Python runs your code — Python ignores them at runtime. But they make your code self-documenting and let tools like `mypy` catch bugs before you run anything.

```python
# WITHOUT type hints — what does this function expect? What does it return?
def process_record(record, threshold):
    if record["amount"] > threshold:
        return True
    return False

# WITH type hints — crystal clear
def process_record(record: dict[str, any], threshold: float) -> bool:
    if record["amount"] > threshold:
        return True
    return False
```

**Common type hint patterns you'll use constantly:**

```python
from typing import Optional

# Basic types
name: str = "Alice"
age: int = 30
salary: float = 75_000.50       # underscores for readability — Python ignores them
is_active: bool = True

# Collections
departments: list[str] = ["HR", "Finance", "Engineering"]
employee: dict[str, str] = {"name": "Alice", "role": "Engineer"}
unique_ids: set[int] = {101, 102, 103}

# Optional — the value might be None
middle_name: Optional[str] = None       # equivalent to str | None in Python 3.10+

# Function signatures
def calculate_bonus(base_salary: float, performance_score: int) -> float:
    """Calculate annual bonus based on performance."""
    multipliers = {1: 0.0, 2: 0.05, 3: 0.10, 4: 0.15, 5: 0.20}
    return base_salary * multipliers.get(performance_score, 0.0)

# Functions that return nothing
def log_event(message: str) -> None:
    print(f"[EVENT] {message}")
```

### 1.5 — Dataclasses

Dataclasses replace the tedious `__init__`, `__repr__`, and `__eq__` boilerplate you'd normally write for data containers.

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

# WITHOUT dataclass — lots of boilerplate
class EmployeeOld:
    def __init__(self, emp_id, name, department, hire_date, salary):
        self.emp_id = emp_id
        self.name = name
        self.department = department
        self.hire_date = hire_date
        self.salary = salary

    def __repr__(self):
        return f"Employee({self.emp_id}, {self.name})"

    def __eq__(self, other):
        return self.emp_id == other.emp_id


# WITH dataclass — Python generates all of the above for you
@dataclass
class Employee:
    emp_id: int
    name: str
    department: str
    hire_date: date
    salary: float
    is_active: bool = True                          # default value
    skills: list[str] = field(default_factory=list)  # mutable defaults need field()
    manager_id: Optional[int] = None

# Usage
alice = Employee(
    emp_id=101,
    name="Alice van den Berg",
    department="Engineering",
    hire_date=date(2023, 3, 15),
    salary=72_000.00,
    skills=["Python", "SQL"],
)

print(alice)
# Employee(emp_id=101, name='Alice van den Berg', department='Engineering',
#          hire_date=datetime.date(2023, 3, 15), salary=72000.0,
#          is_active=True, skills=['Python', 'SQL'], manager_id=None)

print(alice.name)          # Alice van den Berg
print(alice.is_active)     # True
```

**Why `field(default_factory=list)` instead of `= []`?**
Mutable defaults (lists, dicts, sets) are shared across all instances in Python. Using `field(default_factory=list)` creates a fresh list for each instance.

```python
# WRONG — all employees share the same skills list!
@dataclass
class BadEmployee:
    skills: list[str] = []      # This is a bug

# CORRECT
@dataclass
class GoodEmployee:
    skills: list[str] = field(default_factory=list)  # Fresh list per instance
```

### 1.6 — pathlib (Modern File System Work)

Stop using `os.path.join()`. The `pathlib` module is cleaner, more readable, and works the same on every OS.

```python
from pathlib import Path

# Creating paths — the / operator joins path components
data_dir = Path("data")
raw_dir = data_dir / "raw"
output_file = data_dir / "output" / "results.csv"

print(output_file)           # data/output/results.csv  (or data\output\results.csv on Windows)

# Useful properties
print(output_file.name)      # results.csv
print(output_file.stem)      # results
print(output_file.suffix)    # .csv
print(output_file.parent)    # data/output

# Creating directories (parents=True creates any missing parent folders)
raw_dir.mkdir(parents=True, exist_ok=True)

# Listing files
for csv_file in data_dir.glob("*.csv"):         # all CSVs in data/
    print(csv_file)

for csv_file in data_dir.rglob("*.csv"):        # all CSVs in data/ and subfolders
    print(csv_file)

# Checking existence
if output_file.exists():
    print("File found")

# Reading and writing text
config_path = Path("config.txt")
config_path.write_text("debug=true\nlog_level=INFO")
content = config_path.read_text()
print(content)               # debug=true\nlog_level=INFO

# Getting absolute paths
print(Path(".").resolve())   # /Users/you/week1-project
```

**Comparison with the old way:**

```python
import os

# OLD (os.path)
path = os.path.join("data", "raw", "employees.csv")
filename = os.path.basename(path)
exists = os.path.exists(path)

# NEW (pathlib) — same result, much cleaner
path = Path("data") / "raw" / "employees.csv"
filename = path.name
exists = path.exists()
```

---

## Day 2: pandas — The Core of Tabular Data Manipulation (~2.5 hours)

### 2.1 — What is a DataFrame?

A DataFrame is a 2D table — like a spreadsheet or SQL table — where each column can have a different type. It is the single most important data structure you will use as a data engineer.

```python
import pandas as pd

# Creating a DataFrame from a dictionary
data = {
    "emp_id": [101, 102, 103, 104, 105],
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "department": ["Engineering", "HR", "Engineering", "Finance", "HR"],
    "salary": [72000, 58000, 85000, 91000, 62000],
    "hire_date": ["2023-03-15", "2022-07-01", "2021-11-20", "2023-01-10", "2024-02-28"],
}
df = pd.DataFrame(data)

# Always convert date strings to proper datetime objects
df["hire_date"] = pd.to_datetime(df["hire_date"])

print(df)
#    emp_id     name   department  salary  hire_date
# 0     101    Alice  Engineering   72000 2023-03-15
# 1     102      Bob           HR   58000 2022-07-01
# 2     103  Charlie  Engineering   85000 2021-11-20
# 3     104    Diana      Finance   91000 2023-01-10
# 4     105      Eve           HR   62000 2024-02-28
```

### 2.2 — Reading Data from Files

```python
# CSV — the most common format
df = pd.read_csv("data/employees.csv")

# CSV with specific options
df = pd.read_csv(
    "data/employees.csv",
    sep=";",                     # some European CSVs use semicolons
    encoding="utf-8",           # handle special characters
    parse_dates=["hire_date"],  # auto-parse these columns as dates
    dtype={"emp_id": int},      # force column types
    na_values=["N/A", "n/a", ""],  # treat these as missing values
)

# Excel
df = pd.read_excel("data/report.xlsx", sheet_name="Sheet1")

# JSON
df = pd.read_json("data/records.json")

# Parquet — the format you'll use most in data engineering
df = pd.read_parquet("data/employees.parquet")
```

### 2.3 — Inspecting Your Data (Always Do This First)

```python
df.shape              # (5, 5) — 5 rows, 5 columns
df.dtypes             # data type of each column
df.head(3)            # first 3 rows
df.tail(2)            # last 2 rows
df.info()             # column names, types, non-null counts, memory usage
df.describe()         # statistical summary (count, mean, std, min, max, quartiles)
df.isnull().sum()     # count of missing values per column
df.nunique()          # count of unique values per column
df.columns.tolist()   # list of column names
```

**Example output of `df.info()`:**

```
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 5 entries, 0 to 4
Data columns (total 5 columns):
 #   Column      Non-Null Count  Dtype
---  ------      --------------  -----
 0   emp_id      5 non-null      int64
 1   name        5 non-null      object
 2   department  5 non-null      object
 3   salary      5 non-null      int64
 4   hire_date   5 non-null      datetime64[ns]
dtypes: datetime64[ns](1), int64(2), object(2)
memory usage: 328.0+ bytes
```

### 2.4 — Filtering (Selecting Rows Based on Conditions)

```python
# Single condition
engineers = df[df["department"] == "Engineering"]
print(engineers)
#    emp_id     name   department  salary  hire_date
# 0     101    Alice  Engineering   72000 2023-03-15
# 2     103  Charlie  Engineering   85000 2021-11-20

# Multiple conditions — use & (and), | (or), ~ (not)
# IMPORTANT: each condition must be in parentheses
high_paid_engineers = df[
    (df["department"] == "Engineering") & (df["salary"] > 75000)
]
print(high_paid_engineers)
#    emp_id     name   department  salary  hire_date
# 2     103  Charlie  Engineering   85000 2021-11-20

# Using .isin() for multiple values
hr_or_finance = df[df["department"].isin(["HR", "Finance"])]

# Filtering by date
recent_hires = df[df["hire_date"] >= "2023-01-01"]

# String conditions
df[df["name"].str.startswith("A")]
df[df["name"].str.contains("li", case=False)]    # case-insensitive

# Negation — rows where department is NOT Engineering
non_engineers = df[~(df["department"] == "Engineering")]
```

### 2.5 — Selecting Columns

```python
# Single column (returns a Series)
names = df["name"]

# Multiple columns (returns a DataFrame)
subset = df[["name", "salary"]]

# Selecting rows AND columns with .loc (label-based)
df.loc[0:2, ["name", "department"]]     # rows 0-2, only name and department

# Selecting rows AND columns with .iloc (position-based)
df.iloc[0:3, 1:3]                        # first 3 rows, columns at position 1 and 2
```

### 2.6 — Adding and Modifying Columns

```python
# New column from calculation
df["annual_bonus"] = df["salary"] * 0.10

# New column from condition
df["seniority"] = df["hire_date"].apply(
    lambda d: "Senior" if d.year < 2023 else "Junior"
)

# Using .map() for category mapping
dept_codes = {"Engineering": "ENG", "HR": "HRM", "Finance": "FIN"}
df["dept_code"] = df["department"].map(dept_codes)

# Renaming columns
df = df.rename(columns={"emp_id": "employee_id", "name": "full_name"})

# Dropping columns
df = df.drop(columns=["annual_bonus"])
```

### 2.7 — Grouping and Aggregation

This is where pandas becomes truly powerful for data analysis.

```python
# Average salary per department
dept_avg = df.groupby("department")["salary"].mean()
print(dept_avg)
# department
# Engineering    78500.0
# Finance        91000.0
# HR             60000.0
# Name: salary, dtype: float64

# Multiple aggregations at once
dept_stats = df.groupby("department").agg(
    avg_salary=("salary", "mean"),
    max_salary=("salary", "max"),
    headcount=("emp_id", "count"),
    earliest_hire=("hire_date", "min"),
)
print(dept_stats)
#              avg_salary  max_salary  headcount earliest_hire
# department
# Engineering     78500.0       85000          2    2021-11-20
# Finance         91000.0       91000          1    2023-01-10
# HR              60000.0       62000          2    2022-07-01

# Custom aggregation functions
dept_salary_range = df.groupby("department")["salary"].agg(
    ["min", "max", "mean", "std"]
)
```

### 2.8 — Sorting

```python
# Sort by salary descending
df_sorted = df.sort_values("salary", ascending=False)

# Sort by multiple columns
df_sorted = df.sort_values(
    ["department", "salary"],
    ascending=[True, False]        # department A-Z, then salary high-to-low
)
```

### 2.9 — Handling Missing Values

```python
# Create sample data with missing values
messy = pd.DataFrame({
    "name": ["Alice", "Bob", None, "Diana"],
    "salary": [72000, None, 85000, 91000],
    "department": ["Engineering", "HR", "Engineering", None],
})

# Detect missing values
print(messy.isnull())
#     name  salary  department
# 0  False   False       False
# 1  False    True       False
# 2   True   False       False
# 3  False   False        True

# Count missing values per column
print(messy.isnull().sum())
# name          1
# salary        1
# department    1

# Drop rows with ANY missing value
clean = messy.dropna()

# Drop rows only if specific columns are missing
clean = messy.dropna(subset=["name", "salary"])

# Fill missing values
messy["salary"] = messy["salary"].fillna(0)                    # fill with zero
messy["department"] = messy["department"].fillna("Unknown")    # fill with a string
messy["salary"] = messy["salary"].fillna(messy["salary"].mean())  # fill with mean
```

### 2.10 — Writing Data Back to Files

```python
# CSV
df.to_csv("data/output/employees_clean.csv", index=False)  # index=False avoids writing row numbers

# Parquet (preferred for data pipelines — smaller, faster, typed)
df.to_parquet("data/output/employees_clean.parquet", index=False)

# Excel
df.to_excel("data/output/employees_report.xlsx", index=False, sheet_name="Employees")

# JSON
df.to_json("data/output/employees.json", orient="records", indent=2)
```

---

## Day 3: Merging, Reshaping, and numpy (~2.5 hours)

### 3.1 — Merging DataFrames (SQL-style JOINs)

This is one of the most important operations in data engineering — combining data from different sources.

```python
import pandas as pd

# Two DataFrames from different systems
employees = pd.DataFrame({
    "emp_id": [101, 102, 103, 104],
    "name": ["Alice", "Bob", "Charlie", "Diana"],
    "dept_id": [10, 20, 10, 30],
})

departments = pd.DataFrame({
    "dept_id": [10, 20, 40],
    "dept_name": ["Engineering", "HR", "Legal"],
    "budget": [500_000, 200_000, 150_000],
})

# INNER JOIN — only rows where dept_id exists in BOTH tables
inner = pd.merge(employees, departments, on="dept_id", how="inner")
print(inner)
#    emp_id     name  dept_id    dept_name  budget
# 0     101    Alice       10  Engineering  500000
# 1     103  Charlie       10  Engineering  500000
# 2     102      Bob       20           HR  200000
# Diana (dept_id=30) is dropped — no match in departments
# Legal (dept_id=40) is dropped — no match in employees

# LEFT JOIN — keep ALL employees, fill missing department info with NaN
left = pd.merge(employees, departments, on="dept_id", how="left")
print(left)
#    emp_id     name  dept_id    dept_name    budget
# 0     101    Alice       10  Engineering  500000.0
# 1     102      Bob       20           HR  200000.0
# 2     103  Charlie       10  Engineering  500000.0
# 3     104    Diana       30          NaN       NaN   <-- no matching dept

# RIGHT JOIN — keep ALL departments, fill missing employee info with NaN
right = pd.merge(employees, departments, on="dept_id", how="right")

# FULL OUTER JOIN — keep everything from both sides
outer = pd.merge(employees, departments, on="dept_id", how="outer")

# When column names differ between tables
sales = pd.DataFrame({
    "employee_id": [101, 102],
    "total_sales": [150_000, 80_000],
})

merged = pd.merge(
    employees,
    sales,
    left_on="emp_id",       # column name in left table
    right_on="employee_id", # column name in right table
    how="left"
)
```

**How to choose the right join:**

| Join type | Use when... |
|-----------|------------|
| `inner` | You only want rows that match in both tables |
| `left` | You want ALL rows from the left table, with matches from right where available |
| `right` | You want ALL rows from the right table (less common — usually just swap the tables and use left) |
| `outer` | You want ALL rows from both sides, even if they don't match |

### 3.2 — Concatenating DataFrames

Use `concat` when you have multiple DataFrames with the same columns (e.g., monthly files).

```python
# Monthly data files
jan = pd.DataFrame({"month": ["Jan", "Jan"], "revenue": [100, 200]})
feb = pd.DataFrame({"month": ["Feb", "Feb"], "revenue": [150, 250]})
mar = pd.DataFrame({"month": ["Mar", "Mar"], "revenue": [300, 100]})

# Stack them vertically
all_months = pd.concat([jan, feb, mar], ignore_index=True)
print(all_months)
#   month  revenue
# 0   Jan      100
# 1   Jan      200
# 2   Feb      150
# 3   Feb      250
# 4   Mar      300
# 5   Mar      100

# ignore_index=True resets the index to 0,1,2,...
# Without it, you'd get duplicate indices (0,1,0,1,0,1)
```

### 3.3 — Reshaping: Pivot and Melt

```python
# Sample data — long format (each row is one observation)
sales_long = pd.DataFrame({
    "rep": ["Alice", "Alice", "Bob", "Bob"],
    "quarter": ["Q1", "Q2", "Q1", "Q2"],
    "revenue": [50000, 62000, 45000, 48000],
})

# PIVOT — long to wide (like a pivot table in Excel)
sales_wide = sales_long.pivot(
    index="rep",       # rows
    columns="quarter", # becomes new column headers
    values="revenue",  # values to fill in
)
print(sales_wide)
# quarter     Q1     Q2
# rep
# Alice    50000  62000
# Bob      45000  48000

# MELT — wide to long (the reverse of pivot)
sales_back = sales_wide.reset_index().melt(
    id_vars=["rep"],            # columns to keep
    var_name="quarter",         # name for the "header" column
    value_name="revenue",       # name for the "values" column
)
print(sales_back)
#     rep quarter  revenue
# 0  Alice      Q1    50000
# 1    Bob      Q1    45000
# 2  Alice      Q2    62000
# 3    Bob      Q2    48000

# PIVOT TABLE — like pivot but can handle duplicate entries with aggregation
# What if Alice has two Q1 entries?
sales_dupes = pd.DataFrame({
    "rep": ["Alice", "Alice", "Alice", "Bob"],
    "quarter": ["Q1", "Q1", "Q2", "Q1"],
    "revenue": [50000, 12000, 62000, 45000],
})

pt = sales_dupes.pivot_table(
    index="rep",
    columns="quarter",
    values="revenue",
    aggfunc="sum",       # how to combine duplicates: sum, mean, count, etc.
)
print(pt)
# quarter     Q1       Q2
# rep
# Alice    62000  62000.0
# Bob      45000      NaN
```

### 3.4 — numpy Essentials

numpy is the foundation under pandas. You won't use it as much directly, but understanding it helps you work with embeddings, numerical operations, and performance-critical code in later modules.

```python
import numpy as np

# Creating arrays
a = np.array([1, 2, 3, 4, 5])
b = np.array([10, 20, 30, 40, 50])

# Element-wise operations (no loops needed)
print(a + b)          # [11 22 33 44 55]
print(a * 2)          # [ 2  4  6  8 10]
print(a ** 2)         # [ 1  4  9 16 25]
print(a > 3)          # [False False False  True  True]

# Statistical operations
print(np.mean(a))     # 3.0
print(np.std(a))      # 1.4142...
print(np.median(a))   # 3.0
print(np.sum(a))      # 15

# 2D arrays (matrices) — you'll see these with embeddings
matrix = np.array([
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
])
print(matrix.shape)   # (3, 3) — 3 rows, 3 columns
print(matrix[0])      # [1, 2, 3] — first row
print(matrix[:, 1])   # [2, 5, 8] — second column (all rows, column index 1)

# Random numbers (useful for generating test data)
np.random.seed(42)                         # set seed for reproducibility
random_salaries = np.random.normal(
    loc=70000,       # mean
    scale=15000,     # standard deviation
    size=100,        # how many values
)
print(f"Mean: {random_salaries.mean():.0f}")      # ~70000
print(f"Std:  {random_salaries.std():.0f}")        # ~15000

# Cosine similarity — critical for Module 3 (embeddings)
# Measures how similar two vectors are (1.0 = identical, 0.0 = unrelated)
def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    return dot_product / (norm_a * norm_b)

v1 = np.array([1, 2, 3])
v2 = np.array([1, 2, 3])    # identical
v3 = np.array([3, 2, 1])    # different direction

print(cosine_similarity(v1, v2))   # 1.0 (identical)
print(cosine_similarity(v1, v3))   # 0.714... (somewhat similar)
```

---

## Day 4: Logging + Putting It All Together (~2 hours)

### 4.1 — The Logging Module

In production data pipelines, `print()` statements are invisible. Logs are permanent, timestamped, and can be routed to files, monitoring systems, or dashboards. Switch now and never go back.

```python
import logging

# Basic setup — configure once at the top of your script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a logger for your module
logger = logging.getLogger("pipeline")

# The five log levels (from least to most severe)
logger.debug("Detailed debug info — usually turned off in production")
logger.info("Normal operation — 'Pipeline started', '150 rows processed'")
logger.warning("Something unexpected but not fatal — 'Column X has 12% nulls'")
logger.error("Something failed — 'Could not connect to database'")
logger.critical("System-level failure — 'Disk full, cannot write output'")
```

**Output:**

```
2025-01-15 09:30:01 | INFO     | pipeline | Normal operation — 'Pipeline started', '150 rows processed'
2025-01-15 09:30:01 | WARNING  | pipeline | Something unexpected but not fatal — 'Column X has 12% nulls'
2025-01-15 09:30:01 | ERROR    | pipeline | Something failed — 'Could not connect to database'
2025-01-15 09:30:01 | CRITICAL | pipeline | System-level failure — 'Disk full, cannot write output'
```

**Notice:** The `DEBUG` message didn't appear because we set `level=logging.INFO`. Messages below that level are suppressed.

**Logging to a file (essential for production):**

```python
import logging
from pathlib import Path

# Create a logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure with both console and file output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),                              # console output
        logging.FileHandler(log_dir / "pipeline.log"),        # file output
    ],
)

logger = logging.getLogger("pipeline")
logger.info("Pipeline started — log goes to BOTH console and file")
```

**Logging with context (f-strings in log messages):**

```python
rows_processed = 1_247
rows_invalid = 38
duration_sec = 4.2

logger.info(f"Processed {rows_processed} rows in {duration_sec:.1f}s")
logger.warning(f"Found {rows_invalid} invalid rows ({rows_invalid/rows_processed:.1%} of total)")
# 2025-01-15 09:31:15 | INFO     | pipeline | Processed 1247 rows in 4.2s
# 2025-01-15 09:31:15 | WARNING  | pipeline | Found 38 invalid rows (3.0% of total)
```

### 4.2 — python-dotenv for Configuration

Never hardcode file paths, database credentials, or API keys. Use a `.env` file.

```bash
# .env (this file should NEVER be committed to Git — add it to .gitignore)
DATA_DIR=data/raw
OUTPUT_DIR=data/output
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hr_pipeline
LOG_LEVEL=INFO
```

```python
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Access them
data_dir = Path(os.getenv("DATA_DIR", "data/raw"))         # "data/raw" is the default
output_dir = Path(os.getenv("OUTPUT_DIR", "data/output"))
log_level = os.getenv("LOG_LEVEL", "INFO")

print(data_dir)    # data/raw
```

### 4.3 — Complete Mini-Pipeline Example

Here's everything from Days 1–4 combined into a realistic script:

```python
"""
mini_pipeline.py
Reads a messy CSV of employee records, cleans and validates them,
logs every step, and writes clean output to Parquet.
"""
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv

# ─── Configuration ───────────────────────────────────────────────
load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "data/raw"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mini_pipeline")


# ─── Data Model ──────────────────────────────────────────────────
@dataclass
class CleanEmployee:
    emp_id: int
    name: str
    department: str
    salary: float
    hire_date: date
    is_active: bool = True


# ─── Pipeline Functions ─────────────────────────────────────────
def read_raw_data(filepath: Path) -> pd.DataFrame:
    """Read a raw CSV file and return a DataFrame."""
    logger.info(f"Reading raw data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Read {len(df)} rows, {len(df.columns)} columns")
    logger.info(f"Columns: {df.columns.tolist()}")
    return df


def validate_and_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate rows and split into clean and rejected DataFrames.
    Returns (clean_df, rejected_df).
    """
    logger.info("Starting validation...")
    issues: list[dict] = []

    # Track original index for rejection tracking
    df = df.copy()
    df["_original_index"] = df.index

    # --- Check for missing required fields ---
    required_cols = ["emp_id", "name", "department", "salary", "hire_date"]
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            raise ValueError(f"Missing required column: {col}")

    # --- Flag rows with problems ---
    mask_valid = pd.Series(True, index=df.index)

    # Missing names
    missing_name = df["name"].isnull() | (df["name"].str.strip() == "")
    if missing_name.any():
        count = missing_name.sum()
        logger.warning(f"  {count} rows have missing names")
        mask_valid &= ~missing_name

    # Negative or zero salaries
    bad_salary = df["salary"].fillna(0) <= 0
    if bad_salary.any():
        count = bad_salary.sum()
        logger.warning(f"  {count} rows have non-positive salaries")
        mask_valid &= ~bad_salary

    # Unparseable dates
    df["hire_date_parsed"] = pd.to_datetime(df["hire_date"], errors="coerce")
    bad_date = df["hire_date_parsed"].isnull()
    if bad_date.any():
        count = bad_date.sum()
        logger.warning(f"  {count} rows have unparseable hire dates")
        mask_valid &= ~bad_date

    # --- Split ---
    clean_df = df[mask_valid].copy()
    rejected_df = df[~mask_valid].copy()

    # --- Normalize clean data ---
    clean_df["name"] = clean_df["name"].str.strip().str.title()
    clean_df["department"] = clean_df["department"].str.strip().str.title()
    clean_df["salary"] = clean_df["salary"].astype(float).round(2)
    clean_df["hire_date"] = clean_df["hire_date_parsed"]

    # Drop helper columns
    clean_df = clean_df.drop(columns=["_original_index", "hire_date_parsed"])
    rejected_df = rejected_df.drop(columns=["hire_date_parsed"])

    logger.info(
        f"Validation complete: {len(clean_df)} clean, {len(rejected_df)} rejected"
    )
    return clean_df, rejected_df


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-department summary statistics."""
    summary = df.groupby("department").agg(
        headcount=("emp_id", "count"),
        avg_salary=("salary", "mean"),
        max_salary=("salary", "max"),
        min_salary=("salary", "min"),
    ).round(2)
    logger.info(f"Summary computed for {len(summary)} departments")
    return summary


def write_outputs(
    clean_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Write all output files."""
    clean_path = output_dir / "employees_clean.parquet"
    rejected_path = output_dir / "employees_rejected.csv"
    summary_path = output_dir / "department_summary.csv"

    clean_df.to_parquet(clean_path, index=False)
    logger.info(f"Wrote {len(clean_df)} clean records to {clean_path}")

    rejected_df.to_csv(rejected_path, index=False)
    logger.info(f"Wrote {len(rejected_df)} rejected records to {rejected_path}")

    summary_df.to_csv(summary_path)
    logger.info(f"Wrote department summary to {summary_path}")


# ─── Main ────────────────────────────────────────────────────────
def main() -> None:
    logger.info("=" * 60)
    logger.info("Pipeline started")
    start = datetime.now()

    raw_file = DATA_DIR / "employees_raw.csv"

    if not raw_file.exists():
        logger.error(f"Input file not found: {raw_file}")
        return

    df = read_raw_data(raw_file)
    clean_df, rejected_df = validate_and_clean(df)
    summary_df = compute_summary(clean_df)
    write_outputs(clean_df, rejected_df, summary_df, OUTPUT_DIR)

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"Pipeline finished in {elapsed:.2f}s")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
```

---

## Day 5: Practice Exercises + Pydantic Preview (~2 hours)

### 5.1 — Pydantic v2 Preview

Pydantic is the standard for data validation in Python. Where dataclasses are simple containers, Pydantic models actively validate data and raise clear errors when something is wrong. You'll use it heavily starting in the Module 1 project.

```python
from pydantic import BaseModel, Field, field_validator, ValidationError
from datetime import date
from typing import Optional


class EmployeeRecord(BaseModel):
    """Validates a single employee record from raw data."""

    emp_id: int = Field(gt=0, description="Positive integer employee ID")
    name: str = Field(min_length=1, max_length=200)
    department: str
    salary: float = Field(gt=0, description="Must be positive")
    hire_date: date
    is_active: bool = True
    email: Optional[str] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Strip whitespace and title-case the name."""
        return v.strip().title()

    @field_validator("department")
    @classmethod
    def normalize_department(cls, v: str) -> str:
        """Map common abbreviations to full names."""
        mapping = {
            "eng": "Engineering",
            "hr": "Human Resources",
            "fin": "Finance",
            "mkt": "Marketing",
        }
        cleaned = v.strip().lower()
        return mapping.get(cleaned, v.strip().title())

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "@" not in v:
            raise ValueError("Invalid email — must contain @")
        return v


# ── Valid data ───────────────────────────────────────────────────
good_data = {
    "emp_id": 101,
    "name": "  alice van den berg  ",
    "department": "eng",
    "salary": 72000,
    "hire_date": "2023-03-15",
}

employee = EmployeeRecord(**good_data)
print(employee)
# emp_id=101 name='Alice Van Den Berg' department='Engineering'
# salary=72000.0 hire_date=datetime.date(2023, 3, 15) is_active=True email=None

# Convert to dict (for writing to database or JSON)
print(employee.model_dump())


# ── Invalid data — Pydantic raises clear errors ─────────────────
bad_data = {
    "emp_id": -5,                    # negative
    "name": "",                      # empty
    "department": "Engineering",
    "salary": -1000,                 # negative
    "hire_date": "not-a-date",       # unparseable
    "email": "no-at-sign",           # missing @
}

try:
    EmployeeRecord(**bad_data)
except ValidationError as e:
    print(e)
    # 5 validation errors for EmployeeRecord
    # emp_id
    #   Input should be greater than 0 [type=greater_than, ...]
    # name
    #   String should have at least 1 character [type=string_too_short, ...]
    # salary
    #   Input should be greater than 0 [type=greater_than, ...]
    # hire_date
    #   Input should be a valid date [type=date_from_datetime_parsing, ...]
    # email
    #   Value error, Invalid email — must contain @ [type=value_error, ...]


# ── Validating a batch of rows ───────────────────────────────────
import pandas as pd

raw_rows = [
    {"emp_id": 1, "name": "Alice", "department": "eng", "salary": 70000, "hire_date": "2023-01-10"},
    {"emp_id": -2, "name": "", "department": "hr", "salary": -5000, "hire_date": "bad-date"},
    {"emp_id": 3, "name": "Charlie", "department": "fin", "salary": 85000, "hire_date": "2022-06-01"},
]

valid_records = []
invalid_records = []

for i, row in enumerate(raw_rows):
    try:
        record = EmployeeRecord(**row)
        valid_records.append(record.model_dump())
    except ValidationError as e:
        invalid_records.append({"row_index": i, "errors": str(e), "raw_data": row})

print(f"Valid: {len(valid_records)}, Invalid: {len(invalid_records)}")

clean_df = pd.DataFrame(valid_records)
print(clean_df)
#    emp_id     name   department   salary   hire_date  is_active email
# 0       1    Alice  Engineering  70000.0  2023-01-10       True  None
# 1       3  Charlie      Finance  85000.0  2022-06-01       True  None
```

### 5.2 — Practice Exercises

Do these exercises to solidify everything from this week. Each one should take 15–30 minutes.

**Exercise 1: File System Scanner**
Write a script that scans a directory tree and produces a summary DataFrame with columns: `filename`, `extension`, `size_kb`, `last_modified`. Use `pathlib` for all file operations. Sort the result by size descending. Write the output to a CSV.

**Exercise 2: Sales Data Analysis**
Create a DataFrame with 200 rows of mock sales data (use `numpy.random` for random amounts, dates, and regions). Then answer these questions using pandas:
- Total revenue per region
- Which month had the highest average transaction value?
- What percentage of transactions are above $500?
- Pivot table: regions as rows, months as columns, values = total revenue

**Exercise 3: Data Merge Challenge**
Create three DataFrames representing an organization: `employees` (emp_id, name, dept_id), `departments` (dept_id, dept_name, location), and `performance_reviews` (emp_id, quarter, score). Merge them together and produce a report showing each employee's name, department, location, and average performance score. Handle employees with no reviews (they should still appear with a null score).

**Exercise 4: Validation Pipeline**
Create a messy CSV file by hand with these problems: some rows have negative salaries, some have empty names, some have dates in different formats ("2023-01-15", "15/01/2023", "Jan 15 2023"), and some have completely invalid dates ("not-a-date"). Write a pipeline that uses Pydantic to validate each row, separates valid from invalid records, logs a summary of what went wrong, and writes both to separate files.

**Exercise 5: Log File Analyzer**
Generate a fake log file with 500 lines (timestamps, levels, messages). Read it with pandas, parse the timestamps, and answer: how many errors per hour? What's the most common log level? Plot the error rate over time (optional, using matplotlib).

---

## Week 1 Summary — What You Should Be Able To Do

After completing this week, you should be comfortable with:

- Setting up `pyenv` + `venv` for any new project
- Using type hints and dataclasses in all your code
- Using `pathlib` for all file system operations
- Reading CSVs, Excel, JSON, and Parquet with pandas
- Filtering, grouping, aggregating, merging, and reshaping DataFrames
- Handling missing values
- Using numpy for numerical operations
- Using `logging` instead of `print` in all scripts
- Using `python-dotenv` for configuration
- Validating data with Pydantic v2 models and field validators

**Next week (Week 2)** builds directly on this: you'll install PostgreSQL with Docker, learn SQL from scratch, and start working with DuckDB for local analytics over Parquet files.