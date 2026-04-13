# Day 1: What is a Database?

## Welcome to SQL!

In Week 1, you learned to work with data using Python and pandas. You loaded CSV files, cleaned data, and computed statistics. This week, you'll learn a more powerful way to work with data: **relational databases** and **SQL**.

By the end of today, you'll understand what a database is, why we use them instead of CSV files, and you'll write your first SQL queries.

Let's start from the very beginning.

---

## What is a Relational Database?

### The Spreadsheet Analogy

Imagine you have a set of **interconnected spreadsheets**. Each spreadsheet has a specific purpose:

- One sheet lists all **employees** (name, email, salary, department)
- One sheet lists all **departments** (department name, location, budget)
- One sheet lists all **sales** (what was sold, to whom, when, for how much)

In a spreadsheet, you might put a "Department ID" number in the employees sheet that points to a row in the departments sheet. This way, you link the two sheets together without duplicating department information for every employee.

**A relational database works the same way**, but with strict rules and powerful capabilities:

| Spreadsheet Term | Database Term | What it means |
|---|---|---|
| Spreadsheet | **Table** | A single "sheet" of data with rows and columns |
| Row | **Row** (or **Record**) | One entry in the table (e.g., one employee) |
| Column | **Column** (or **Field**) | One attribute (e.g., the salary column) |
| Tab name | **Table name** | How you refer to the table (e.g., `employees`) |
| Link between sheets | **Relationship** | A column that points to another table's unique identifier |

The "relational" part means these tables can **reference each other**. That's the whole idea — data is split across tables (to avoid duplication) and then reconnected when you need the full picture.

---

## Why Not Just Use CSV Files?

In Week 1, you worked with CSV files using pandas. CSVs are great for simple tasks, but they have serious limitations. Let's look at **four concrete problems** that databases solve.

### Problem 1: No Concurrent Access

**The scenario:** Two scripts try to write to `employees.csv` at the same time.

**What happens:** The second script overwrites the first script's changes, or worse, both write simultaneously and corrupt the file. You lose data.

**How a database solves it:** A database is a **server** — a background program that manages all access. When two scripts try to write, the database queues them up. Script A writes, then Script B writes. No corruption, no data loss. It's like having a librarian who makes sure only one person writes in the guestbook at a time.

### Problem 2: No Integrity Rules

**The scenario:** You accidentally put the text `"banana"` in the `salary` column of your CSV.

**What happens:** pandas reads it fine. Your analysis crashes three hours later when it tries to compute `AVG(salary)` and hits `"banana"`. Good luck debugging that.

**How a database solves it:** You define **data types** for each column. If `salary` is a `NUMERIC` column, the database **refuses** to accept `"banana"`. It gives you an error immediately, right when you try to insert the bad data. Errors that happen early are easy to fix.

### Problem 3: No Built-in Relationships

**The scenario:** You want to find all employees in the Engineering department, but the department name is only in `departments.csv`, not in `employees.csv`.

**What happens:** You write custom Python code every time:
```python
# Load both files
employees = pd.read_csv("employees.csv")
departments = pd.read_csv("departments.csv")
# Merge them
merged = employees.merge(departments, left_on="department_id", right_on="dept_id")
# Filter
engineering = merged[merged["dept_name"] == "Engineering"]
```

**How a database solves it:** You write one line of SQL:
```sql
SELECT * FROM employees JOIN departments ON employees.department_id = departments.dept_id
WHERE departments.dept_name = 'Engineering';
```

The database **knows** how the tables are related. You just ask for what you want.

### Problem 4: No Efficient Querying

**The scenario:** You have a CSV file with 10 million rows. You want to find the one employee named "Alice Chen."

**What happens:** pandas must **read the entire file into memory** — all 10 million rows — just to find Alice. This is slow and memory-hungry.

**How a database solves it:** With an **index** (like the index at the back of a book), the database can jump directly to "Alice Chen" without reading anything else. It's the difference between reading every page of a 1000-page book to find one mention versus looking it up in the index.

We'll cover indexes in depth on Day 5.

---

## Key Concepts, Explained from Zero

### Table, Row, Column

These are the building blocks:

- **Table**: A named collection of related data (like `employees`)
- **Row** (Record): One entry in the table (one specific employee)
- **Column** (Field): One type of information about each entry (e.g., `salary`)

```
Table: employees
┌────────┬───────────┬───────────┬────────────┬──────────┐
│ emp_id │ first_name│ last_name │  salary    │ dept_id  │
├────────┼───────────┼───────────┼────────────┼──────────┤
│   1    │   Alice   │   Chen    │  145000.00 │    1     │  ← Row 1 (one employee)
│   2    │    Bob    │ Martinez  │  125000.00 │    1     │  ← Row 2 (another employee)
└────────┴───────────┴───────────┴────────────┴──────────┘
  ↑          ↑           ↑          ↑            ↑
 Column    Column      Column     Column       Column
```

### Primary Key: The Unique Identifier

Every table should have a **primary key** — a column whose value is **unique for every row** and **never NULL**.

In our `employees` table, that's `emp_id`. No two employees share the same `emp_id`. It's like a social security number or student ID.

**Why do we need it?** So we can reference any specific row unambiguously. If I say "employee #3," there's no confusion about which employee I mean.

**In SQL:**
```sql
CREATE TABLE employees (
    emp_id SERIAL PRIMARY KEY,  -- ← This declares the primary key
    first_name VARCHAR(50),
    ...
);
```

`SERIAL` means "automatically generate a unique number for each new row." You don't have to manage the IDs yourself.

### Foreign Key: The Pointer to Another Table

A **foreign key** is a column that contains values pointing to a **primary key in another table**.

In `employees`, the `department_id` column is a foreign key. Its values (1, 2, 3, etc.) correspond to `dept_id` in the `departments` table.

```
employees table                    departments table
┌─────────┬──────────┐            ┌─────────┬─────────────┐
│ emp_id  │ dept_id  │────points──│ dept_id │  dept_name  │
├─────────┼──────────┤   to ──────┼─────────┼─────────────┤
│    1    │    1     │───────────→│    1    │ Engineering │
│    2    │    1     │───────────→│    2    │    HR       │
│    9    │    2     │───────────→│    3    │   Finance   │
└─────────┴──────────┘            └─────────┴─────────────┘
```

This is how tables are "related" — hence **relational database**.

**In SQL:**
```sql
CREATE TABLE employees (
    emp_id SERIAL PRIMARY KEY,
    department_id INT REFERENCES departments(dept_id),  -- ← Foreign key
    ...
);
```

`REFERENCES departments(dept_id)` tells the database: "This column points to the `dept_id` column in the `departments` table." The database enforces this — you can't put `department_id = 99` if there's no department 99.

### Schema: A Namespace for Tables

Think of a **schema** like a **folder** inside your database. It groups related tables together.

Our database uses a schema called `company`. So the full name of the employees table is `company.employees`.

```
Database: week2_db
├── Schema: company
│   ├── employees
│   ├── departments
│   ├── products
│   └── sales
└── Schema: public (default, we won't use it much)
```

**Why use schemas?** If you have multiple projects in the same database, schemas keep them separate. `company.employees` won't conflict with `hr.employees` because they're in different schemas.

### SQL: The Language for Talking to Databases

**SQL** = **Structured Query Language**. It's the universal language for relational databases.

The beautiful thing about SQL: **the same language works across PostgreSQL, MySQL, SQLite, SQL Server, Oracle, and more.** The core syntax (`SELECT`, `FROM`, `WHERE`, `JOIN`) is nearly identical everywhere. Once you learn SQL, you can work with almost any database system.

A SQL **query** is how you ask the database a question. For example:
- "Give me all employees in the Engineering department"
- "What's the average salary per department?"
- "Which employee made the most sales last month?"

---

## What is PostgreSQL?

**PostgreSQL** (often called "Postgres") is the most popular open-source relational database in the world. It's used by startups, Fortune 500 companies, governments, and researchers.

**Key facts:**
- It runs as a **server** — a background process that listens for connections
- You send it SQL commands, it processes them and returns results
- It's **ACID-compliant** — meaning it guarantees your data is safe even if the power goes out mid-write
- It's **free** and open-source

**How it works in simple terms:**

```
Your Python Script          PostgreSQL Server
        │                        │
        │  "SELECT * FROM        │
        │   employees            │
        │   WHERE salary > 80000"│
        │───────────────────────→│
        │                        │  (looks up the data)
        │                        │
        │  ←─────────────────────│
        │  [Alice, 145000]       │
        │  [Bob, 125000]         │
        │  [Nathan, 135000]      │
        │                        │
```

You send a query → PostgreSQL finds the matching rows → it sends them back to you.

---

## What is Docker and Why Are We Using It?

**Docker** lets you run software in isolated **containers** — think of them as lightweight virtual machines.

### The Problem Without Docker

Installing PostgreSQL directly on your Linux system can be messy:
- It might conflict with other software
- Configuration files scatter across your system
- When you're done learning, uninstalling is tedious
- Different projects might need different PostgreSQL versions

### The Docker Solution

With Docker, PostgreSQL runs in its own container:
- Everything it needs is packaged inside the container
- It doesn't touch your main system
- When you're done: `docker compose down` removes everything cleanly
- The same container runs identically on any machine

**docker-compose** is a YAML file that describes which containers to start and how to configure them. Ours starts two containers:
1. **PostgreSQL** — the database server
2. **pgAdmin** — a web interface for managing the database (optional, but handy)

### Forward Connection

> **Looking ahead:** The SQL you learn this week is the same SQL you'll use in **Week 6 with dbt** (a tool that generates SQL transformations for data pipelines). It's the same SQL behind **pgvector in Module 3** when you store AI embeddings in PostgreSQL. And it's the same SQL you'll write in every data engineering role for the rest of your career. SQL is a forever skill.

---

## What's Next?

Now that you understand the concepts, it's time to get hands-on. In the notebook `02_first_queries.ipynb`, you will:

1. Connect to the PostgreSQL database from Python
2. Write your first `SELECT` queries
3. Filter data with `WHERE`
4. Sort results with `ORDER BY`
5. Limit results with `LIMIT`
6. Use string and date functions

Open `02_first_queries.ipynb` and let's start querying!
