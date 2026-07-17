# SQL Aggregation: From Rows to Insights

## Why Aggregation Matters

So far, your SQL queries have returned rows that already exist in the database. Every row in the result came from a real row in a table. But in data engineering, you rarely just "list" data. You **summarize** it.

> How many orders did we process last month? What is the average salary per department? Which product category generates the most revenue?

These questions do not have a row in any table. They require you to **collapse many rows into a single value**. That is what aggregation does.

---

## 1. Aggregate Functions: Collapsing Rows into Values

An aggregate function takes a column with many values and reduces them to one. Think of it like a mathematical operation that squashes a vertical column of numbers into a single cell.

### The Five Core Functions

| Function | What it does | Analogy |
|---|---|---|
| `COUNT()` | Counts rows | Counting heads in a room |
| `SUM()` | Adds all values | Running a cash register total |
| `AVG()` | Calculates the mean | Splitting a dinner bill evenly |
| `MIN()` | Finds the smallest value | Finding the cheapest item on a menu |
| `MAX()` | Finds the largest value | Finding the most expensive item on a menu |

### Example: A Simple Employees Table

```
employees
+----+----------+------------+----------+
| id | name     | department | salary   |
+----+----------+------------+----------+
|  1 | Alice    | Sales      |  75000   |
|  2 | Bob      | Sales      |  82000   |
|  3 | Carol    | IT         |  91000   |
|  4 | Dave     | IT         |  88000   |
|  5 | Eve      | HR         |  70000   |
+----+----------+------------+----------+
```

Without aggregation, you can list salaries:

```sql
SELECT salary FROM employees;
```
```
salary
------
75000
82000
91000
88000
70000
```

With aggregation, you collapse those five rows into one:

```sql
SELECT 
    COUNT(*) AS total_employees,
    SUM(salary) AS total_payroll,
    AVG(salary) AS average_salary,
    MIN(salary) AS lowest_salary,
    MAX(salary) AS highest_salary
FROM employees;
```
```
total_employees | total_payroll | average_salary | lowest_salary | highest_salary
----------------+---------------+----------------+---------------+---------------
      5         |    406000     |    81200.00    |     70000     |     91000
```

Five rows became one. That is the essence of every aggregate function.

---

## 2. GROUP BY: The Card Sorting Mental Model

Aggregate functions become powerful when you combine them with `GROUP BY`. The best way to understand GROUP BY is a physical analogy.

### The Card Sorting Analogy

> Imagine you have a deck of playing cards spread across a table. Your task is to count how many cards are in each suit.
> 
> **Step 1:** You physically sort the cards into four piles: Hearts, Diamonds, Clubs, Spades.
> 
> **Step 2:** You count the cards in each pile.
> 
> That is GROUP BY. Step 1 is the "grouping." Step 2 is the "aggregation."

```
Before GROUP BY (all mixed):
  [A-h] [K-d] [3-c] [7-h] [Q-s] [5-d] [2-c] ...

After GROUP BY suit (sorted into piles):
  Hearts:    [A-h] [7-h] ...       --> COUNT = ?
  Diamonds:  [K-d] [5-d] ...       --> COUNT = ?
  Clubs:     [3-c] [2-c] ...       --> COUNT = ?
  Spades:    [Q-s] ...             --> COUNT = ?
```

### SQL Translation

The card sorting analogy maps directly to SQL:

```sql
SELECT 
    department,
    COUNT(*) AS employee_count,
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department;
```

What happens inside the database engine:

```
Step 1 - GROUP BY department (sort into piles):
  
  Sales:  [Alice, 75000] [Bob, 82000]
  IT:     [Carol, 91000] [Dave, 88000]
  HR:     [Eve, 70000]

Step 2 - Apply aggregates to each pile:
  
  Sales:  COUNT = 2,  AVG = 78500
  IT:     COUNT = 2,  AVG = 89500
  HR:     COUNT = 1,  AVG = 70000

Final result:
  department | employee_count | avg_salary
  -----------+----------------+-----------
  Sales      |       2        |  78500
  IT         |       2        |  89500
  HR         |       1        |  70000
```

The `GROUP BY department` clause sorts rows into department "piles." Then `COUNT(*)` and `AVG(salary)` run independently inside each pile.

---

## 3. The Golden Rule of GROUP BY

There is one rule in SQL that causes more student errors than any other. Memorize it:

> **Every column in your SELECT list must either be inside an aggregate function OR appear in the GROUP BY clause.**

### Why Does This Rule Exist?

Consider this broken query:

```sql
-- BROKEN - this will throw an error
SELECT 
    department,
    name,
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department;
```

Why does this fail? After grouping by department, the database has collapsed multiple rows into one row per department. The `AVG(salary)` makes sense -- it is one number per group. The `department` makes sense -- it is the group label. But `name`? There are multiple names in each department. Which one should SQL display?

```
For the "Sales" group, which name do you show?
  Sales pile: [Alice, Bob]
  
  department | name | avg_salary
  -----------+------+-----------
  Sales      | ???  |  78500
```

SQL refuses to guess. It demands you either:
- Put `name` in an aggregate function: `MAX(name)`, `MIN(name)` -- picks one deterministically
- Put `name` in GROUP BY: `GROUP BY department, name` -- creates finer-grained groups

### The Valid Versions

**Option A: Remove `name` from SELECT**

```sql
SELECT 
    department,
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department;
```

**Option B: Aggregate `name`**

```sql
SELECT 
    department,
    MAX(name) AS last_alphabetically,
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department;
```

**Option C: Add `name` to GROUP BY** (changes the grouping granularity)

```sql
SELECT 
    department,
    name,
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department, name;
-- Now each row is one person, so AVG(salary) = their actual salary.
-- Technically valid, but semantically pointless.
```

**Remember the rule as a checklist:**

```
For each column in SELECT:
  [ ] Is it inside COUNT, SUM, AVG, MIN, MAX?  --> OK
  [ ] Is it in the GROUP BY clause?             --> OK
  [ ] Neither?                                   --> ERROR
```

---

## 4. Three Types of COUNT

COUNT looks simple, but it has three distinct behaviors that produce different numbers. This is a frequent source of confusion.

### The Sales Data with NULLs

Consider this sales table where some regions are unknown (NULL):

```
sales
+----+------------+--------+-------+
| id | product    | region | price |
+----+------------+--------+-------+
|  1 | Widget     | North  |   10  |
|  2 | Gadget     | South  |   25  |
|  3 | Widget     | North  |   10  |
|  4 | Gizmo      | NULL   |   15  |
|  5 | Gadget     | South  |   25  |
|  6 | Widget     | NULL   |   10  |
|  7 | Doohickey  | East   |   30  |
+----+------------+--------+-------+
```

### COUNT(*) -- Count Every Row

```sql
SELECT COUNT(*) AS total_rows FROM sales;
```
```
total_rows
----------
    7
```

`COUNT(*)` counts **rows**, not values. It does not care what is inside the row. It counts rows with NULLs, rows with zeros, rows with anything. It answers: "How many rows exist in this table?"

### COUNT(column_name) -- Count Non-NULL Values

```sql
SELECT COUNT(region) AS known_regions FROM sales;
```
```
known_regions
-------------
      5
```

`COUNT(region)` counts only rows where `region` is **not NULL**. The two rows with NULL regions are silently skipped. It answers: "How many rows have a known region?"

Notice: 5, not 7. Two rows vanished from the count because their region is NULL.

### COUNT(DISTINCT column_name) -- Count Unique Non-NULL Values

```sql
SELECT COUNT(DISTINCT region) AS unique_regions FROM sales;
```
```
unique_regions
--------------
      3
```

`COUNT(DISTINCT region)` first removes NULLs, then removes duplicates, then counts what remains. The regions are: North, South, North, South, East. After removing duplicates: North, South, East. Count = 3.

### All Three Side by Side

```sql
SELECT 
    COUNT(*) AS total_rows,
    COUNT(region) AS known_regions,
    COUNT(DISTINCT region) AS unique_regions
FROM sales;
```
```
total_rows | known_regions | unique_regions
-----------+---------------+---------------
     7     |       5       |       3
```

Three different numbers from the same column. This is not a bug -- each variant answers a different business question:

- `COUNT(*)` = "How many sales transactions occurred?" (7)
- `COUNT(region)` = "How many sales have a recorded region?" (5)
- `COUNT(DISTINCT region)` = "How many distinct regions did we sell to?" (3)

---

## 5. WHERE vs HAVING: The Timing Rule

This is the second most confusing topic for SQL beginners. Both WHERE and HAVING filter data, but they run at **different times** in the query execution order.

### The Execution Order

SQL does not execute clauses in the order you write them. It executes them in this order:

```
1. FROM        -- Which table?
2. WHERE       -- Filter individual rows
3. GROUP BY    -- Sort rows into piles
4. HAVING      -- Filter entire piles
5. SELECT      -- Choose columns
6. ORDER BY    -- Sort the result
```

The critical insight: **WHERE runs before GROUP BY. HAVING runs after GROUP BY.**

### Why WHERE Cannot Use Aggregate Functions

Suppose you want to find departments where the average salary exceeds 80,000. Your instinct might be:

```sql
-- BROKEN - this will throw an error
SELECT department, AVG(salary) AS avg_salary
FROM employees
WHERE AVG(salary) > 80000
GROUP BY department;
```

This fails because WHERE executes **before** GROUP BY. At the time WHERE runs, rows have not yet been grouped, so `AVG(salary)` does not exist yet.

```
Execution timeline of the broken query:

1. FROM employees         --> All 5 rows loaded
2. WHERE AVG(salary)>80K  --> ERROR! No groups exist yet.
   (The engine has not reached step 3)
3. GROUP BY department    --> Never reached
```

### The Correct Version with HAVING

```sql
SELECT 
    department, 
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department
HAVING AVG(salary) > 80000;
```
```
department | avg_salary
-----------+-----------
IT         |   89500
```

HAVING works because it runs **after** GROUP BY has created the department piles and **after** AVG(salary) has been calculated for each pile.

```
Execution timeline of the correct query:

1. FROM employees         --> All 5 rows loaded
2. GROUP BY department    --> 3 piles: Sales, IT, HR
3. Calculate AVG per pile --> Sales=78500, IT=89500, HR=70000
4. HAVING AVG > 80000     --> Filter piles: only IT survives
5. SELECT                 --> Return department, avg_salary for IT
```

### WHERE and HAVING Together

They can coexist in the same query, serving different purposes:

```sql
SELECT 
    department,
    AVG(salary) AS avg_salary
FROM employees
WHERE salary > 70000          -- Filter individual employees first
GROUP BY department
HAVING COUNT(*) >= 2;          -- Then filter groups with fewer than 2 people
```

```
Step 1 - WHERE salary > 70000 (remove Eve, who earns 70000):
  Sales: [Alice 75000, Bob 82000]
  IT:    [Carol 91000, Dave 88000]
  HR:    []  (empty - Eve was filtered out)

Step 2 - GROUP BY + AVG:
  Sales: avg = 78500
  IT:    avg = 89500

Step 3 - HAVING COUNT(*) >= 2:
  Sales: 2 people --> KEEP
  IT:    2 people --> KEEP

Result:
  department | avg_salary
  -----------+-----------
  Sales      |   78500
  IT         |   89500
```

### Quick Decision Guide

| Question | Use |
|---|---|
| Filter individual rows before grouping? | WHERE |
| Filter groups after aggregation? | HAVING |
| Condition uses COUNT, SUM, AVG, etc.? | HAVING |
| Condition uses column values directly? | WHERE |

---

## 6. CTEs (WITH Clause): Named Query Variables

A Common Table Expression (CTE) is one of the most important readability tools in SQL. It lets you name a query result and reference it later, as if it were a table.

### The Core Idea

> A CTE is like saving a query result into a temporary variable. Instead of nesting one SELECT inside another, you define the inner query at the top, give it a name, and use that name in your main query.

### Syntax

```sql
WITH cte_name AS (
    -- Any valid SELECT query
    SELECT column1, column2
    FROM some_table
    WHERE condition
)
SELECT *
FROM cte_name;
```

### Before CTEs: The Nested Subquery Approach

```sql
SELECT department, avg_salary
FROM (
    SELECT department, AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department
) AS dept_avg
WHERE avg_salary > 80000;
```

This query nests a SELECT inside the FROM clause. The reader must start reading from the middle, understand the inner query, then jump back out to understand what the outer query does. It is inside-out reading.

### After CTEs: The Linear Approach

```sql
WITH department_salaries AS (
    SELECT 
        department,
        AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department
)
SELECT department, avg_salary
FROM department_salaries
WHERE avg_salary > 80000;
```

The CTE version reads top to bottom like a story:
1. "First, compute average salary per department."
2. "Then, from those results, show departments above 80,000."

### Multiple CTEs: Building a Pipeline

CTEs can be chained. Each one can reference the previous ones:

```sql
WITH department_avg AS (
    SELECT 
        department,
        AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department
),
company_avg AS (
    SELECT AVG(salary) AS overall_avg
    FROM employees
),
above_average_depts AS (
    SELECT 
        d.department,
        d.avg_salary,
        c.overall_avg
    FROM department_avg d, company_avg c
    WHERE d.avg_salary > c.overall_avg
)
SELECT * FROM above_average_depts;
```

Each CTE builds on the previous one, creating a readable data pipeline. This is exactly how data engineers think about transformations: step by step, each named clearly.

### Connection to Modern Data Engineering

> **Looking ahead to Week 6:** When you learn dbt (data build tool), every model you write will use CTEs exactly like the examples above. dbt generates SQL, and that SQL is almost always structured as a chain of CTEs. The `department_avg`, `company_avg`, and `above_average_depts` pattern you see here is the same pattern professional analytics engineers use in production dbt projects. The only difference is that in dbt, each CTE might become its own model file. Learning CTEs now means you are already learning the dbt mental model.

---

## 7. Subqueries: Queries Inside Queries

A subquery is a SELECT statement nested inside another SELECT statement. They appear in three locations, each serving a different purpose.

### Subquery in WHERE: Filtering by a Computed Value

This is the most common use. You need a single value from the database to use as a filter, but you do not know the value in advance.

```sql
SELECT name, salary, department
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```

The inner query runs first and produces one number:

```
Step 1 - Subquery executes:
  SELECT AVG(salary) FROM employees
  Result: 81200

Step 2 - Outer query uses that number:
  SELECT name, salary, department
  FROM employees
  WHERE salary > 81200

Result:
  name  | salary | department
  ------+--------+-----------
  Bob   |  82000 | Sales
  Carol |  91000 | IT
  Dave  |  88000 | IT
```

This is a **non-correlated subquery**: the inner query runs once, produces a result, and the outer query uses it.

### Subquery in FROM: Treating a Query Result as a Table

You can use a subquery anywhere a table name would go:

```sql
SELECT 
    department,
    avg_salary
FROM (
    SELECT 
        department,
        AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department
) AS dept_avg
ORDER BY avg_salary DESC;
```

The subquery creates a temporary result set that the outer query treats like a real table. This is functionally identical to a CTE, just written in a different order.

### Correlated Subqueries: The Inner Query Depends on the Outer Query

A correlated subquery references a column from the outer query. This means it cannot run independently -- it must re-execute for every row of the outer query.

```sql
SELECT 
    name,
    salary,
    department,
    (SELECT AVG(salary) 
     FROM employees e2 
     WHERE e2.department = employees.department
    ) AS dept_avg_salary
FROM employees;
```

The inner query calculates the average salary **for the same department as the current row**. It re-runs for each employee:

```
For Alice (Sales):  subquery computes AVG where department = 'Sales'  --> 78500
For Bob (Sales):    subquery computes AVG where department = 'Sales'  --> 78500
For Carol (IT):     subquery computes AVG where department = 'IT'     --> 89500
For Dave (IT):      subquery computes AVG where department = 'IT'     --> 89500
For Eve (HR):       subquery computes AVG where department = 'HR'     --> 70000

Result:
  name  | salary | department | dept_avg_salary
  ------+--------+------------+----------------
  Alice |  75000 | Sales      |     78500
  Bob   |  82000 | Sales      |     78500
  Carol |  91000 | IT         |     89500
  Dave  |  88000 | IT         |     89500
  Eve   |  70000 | HR         |     70000
```

### Correlated vs Non-Correlated: The Difference

| | Non-Correlated | Correlated |
|---|---|---|
| **Dependency** | Independent of outer query | References outer query's columns |
| **Execution** | Runs once | Runs once per outer row |
| **Performance** | Fast | Can be slow on large tables |
| **Readability** | Straightforward | Harder to follow |

### Non-Correlated Subquery Example

```sql
-- Inner query has no reference to the outer query.
-- It runs once, returns 81200.
SELECT name FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```

### Correlated Subquery Example

```sql
-- Inner query references e.department from the outer query.
-- It runs once for each employee row.
SELECT name FROM employees e
WHERE salary > (
    SELECT AVG(salary) FROM employees e2
    WHERE e2.department = e.department
);
```

Notice the `e.department` reference inside the inner query. That is what makes it correlated. The inner query cannot run on its own -- it needs the outer query's row context.

---

## 8. When to Use CTEs vs Subqueries

Both CTEs and subqueries let you break a complex query into pieces. But they are not equally good at everything.

### Default to CTEs

In modern SQL, CTEs should be your default choice. They offer:

- **Top-to-bottom readability**: Define data transformations in the order they happen.
- **Reusability**: Reference the same CTE multiple times in the main query.
- **Debuggability**: You can `SELECT * FROM cte_name` to inspect intermediate results.
- **Maintainability**: Other engineers can read and modify your query without untangling nested parentheses.

```sql
-- CTE: clear, reusable, debuggable
WITH high_earners AS (
    SELECT * FROM employees WHERE salary > 85000
)
SELECT * FROM high_earners
WHERE department = 'IT';
```

### When Subqueries Are Fine

Use a subquery when it is truly a simple, single-value lookup:

```sql
-- Subquery is natural here: one number, used once, in WHERE
SELECT name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```

This is a one-liner that is immediately clear. Converting it to a CTE would add lines without adding clarity:

```sql
-- Over-engineered for this simple case
WITH avg_sal AS (
    SELECT AVG(salary) AS val FROM employees
)
SELECT name, salary
FROM employees, avg_sal
WHERE salary > avg_sal.val;
```

### Decision Matrix

| Situation | Recommended Approach |
|---|---|
| Simple single-value filter in WHERE | Subquery |
| Multi-step data transformation | CTE |
| Same intermediate result used multiple times | CTE |
| Query result used as a table in FROM | CTE (more readable) |
| Correlated row-by-row comparison | Correlated subquery or JOIN |
| Pipeline of transformations (dbt style) | CTE chain |

### The Golden Rule of Readability

> **If you have to read a query more than once to understand it, rewrite it with CTEs.** Your future self (and your teammates) will thank you.

---

## Practice Checklist

Test your understanding by writing queries for these tasks:

1. Count how many employees work in each department.
2. Find departments where the average salary is above the company-wide average. (Hint: use a CTE or subquery.)
3. Count total sales, sales with a known region, and distinct regions from the sales table.
4. Find employees who earn more than everyone in their own department. (Hint: correlated subquery or HAVING.)
5. Rewrite this nested subquery as a CTE chain:

```sql
SELECT department, avg_sal
FROM (
    SELECT department, AVG(salary) AS avg_sal
    FROM employees
    WHERE hire_date > '2020-01-01'
    GROUP BY department
) AS recent
WHERE avg_sal > 75000;
```

---

## Key Takeaways

- **Aggregate functions** collapse many rows into one value: COUNT, SUM, AVG, MIN, MAX.
- **GROUP BY** sorts rows into piles, then aggregates run inside each pile independently.
- **The golden rule**: every SELECT column must be aggregated or in GROUP BY.
- **Three COUNTs**: `COUNT(*)` counts all rows, `COUNT(col)` counts non-NULLs, `COUNT(DISTINCT col)` counts unique non-NULLs.
- **WHERE filters rows; HAVING filters groups.** WHERE runs before GROUP BY; HAVING runs after.
- **CTEs** are named, reusable query blocks. They are the foundation of readable SQL and the pattern used in modern tools like dbt.
- **Subqueries** work in WHERE, FROM, and SELECT. Correlated subqueries reference outer query columns and re-run per row.
- **Default to CTEs** for readability. Use subqueries for simple single-value lookups.
