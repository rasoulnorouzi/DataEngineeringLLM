# Window Functions in SQL

## The Problem Window Functions Solve

Imagine you are a manager and you want a report that shows **every single employee** on a separate line, but next to each employee, you also want to see the **average salary of their entire department**. At first glance, this seems simple. But with the SQL tools you have so far, it is surprisingly painful.

Here is why. Think of your table as a spreadsheet with 100 rows -- one per employee. If you use `GROUP BY department_id`, SQL **collapses** those 100 rows into however many departments exist -- maybe 5 rows. You get one row per department with the average salary. But now you have lost the individual employees. You cannot see each person's name or their personal salary anymore.

```
Original table (100 rows)          After GROUP BY department_id (5 rows)
+----+-------+-------+------+        +-------+--------------+
| id | name  | dept  | sal  |        | dept  | avg_salary   |
+----+-------+-------+------+        +-------+--------------+
|  1 | Alice | Sales | 5000 |        | Sales | 4800         |
|  2 | Bob   | Sales | 4600 |   =>   | HR    | 5200         |
|  3 | Carol | HR    | 5200 |        | IT    | 6100         |
|  4 | Dave  | IT    | 6000 |        | ...   | ...          |
|... |  ...  | ...   | ...  |        +-------+--------------+
+----+-------+-------+------+

Problem: Individual employee details are GONE.
```

This is the fundamental limitation of `GROUP BY`: it **aggregates and collapses**. You trade row-level detail for summary statistics. You cannot have both -- until window functions.

Window functions solve this exact problem. They compute an aggregate value (like `AVG`, `SUM`, `COUNT`) but **attach it as a new column** on every original row. No rows are collapsed. You get the detail AND the summary, side by side.

```
With a window function (still 100 rows)
+----+-------+-------+------+------------+
| id | name  | dept  | sal  | dept_avg   |
+----+-------+-------+------+------------+
|  1 | Alice | Sales | 5000 | 4800       |
|  2 | Bob   | Sales | 4600 | 4800       |
|  3 | Carol | HR    | 5200 | 5200       |
|  4 | Dave  | IT    | 6000 | 6100       |
+----+-------+-------+------+------------+

Every row survives. The aggregate rides along as a new column.
```

In Week 6, you will use window functions inside dbt models to compute running metrics -- like running revenue or month-over-month growth -- as part of automated data pipelines. The output of one model becomes the input of the next, and window functions are the workhorse for these calculations.

---

## Side-by-Side Comparison: Old Way vs Window Function

Let us see the exact same question answered two different ways. The contrast will make the value of window functions obvious.

**Question:** Show each employee along with their department's average salary.

### The Old Way: GROUP BY + JOIN

Without window functions, you need two separate steps. First, compute department averages. Second, join them back to the employee table.

```sql
-- Step 1: Compute averages in a subquery or CTE
-- Step 2: JOIN back to the original table
SELECT
    e.employee_id,
    e.employee_name,
    e.department_id,
    e.salary,
    d.dept_avg_salary
FROM employees e
JOIN (
    SELECT department_id, AVG(salary) AS dept_avg_salary
    FROM employees
    GROUP BY department_id
) d ON e.department_id = d.department_id;
```

Read through that. It is **ten lines** of SQL. You have to create a subquery, group inside it, then join it back. It works, but it is verbose and harder to read.

### The Window Function Way

```sql
SELECT
    employee_id,
    employee_name,
    department_id,
    salary,
    AVG(salary) OVER(PARTITION BY department_id) AS dept_avg_salary
FROM employees;
```

**That is it.** Five lines. One function call. No subquery, no join, no group-by inside a group-by. The `OVER(PARTITION BY department_id)` clause tells SQL: "compute the average salary, but do it separately for each department, and put the result on every row."

This is the "aha" moment. Window functions replace a multi-step pattern with a single, declarative line. As your queries grow more complex -- with multiple aggregates, rankings, and running totals -- this conciseness becomes invaluable.

---

## The OVER() Clause: Your Window Into the Data

The `OVER()` clause is what turns a regular aggregate function into a window function. Without `OVER()`, `AVG(salary)` collapses rows. With `OVER()`, `AVG(salary) OVER(...)` computes a value for each row.

Think of `OVER()` as defining a **window** -- a subset of rows -- that the function looks at when computing its result. The function slides this window across your data.

### Three levels of OVER()

```sql
-- Level 1: Empty OVER() -- the window is ALL rows
SELECT
    employee_name,
    salary,
    AVG(salary) OVER() AS overall_avg
FROM employees;
```

With an empty `OVER()`, the window includes every row in the result set. Every employee sees the same number -- the company-wide average.

```
+-------+--------+-------------+
| name  | salary | overall_avg |
+-------+--------+-------------+
| Alice |  5000  |  5400       |
| Bob   |  4600  |  5400       |
| Carol |  5200  |  5400       |
| Dave  |  6000  |  5400       |
| Eve   |  6200  |  5400       |
+-------+--------+-------------+
Same value on every row. The window = entire table.
```

```sql
-- Level 2: OVER(PARTITION BY ...) -- the window is a group
SELECT
    employee_name,
    department_id,
    salary,
    AVG(salary) OVER(PARTITION BY department_id) AS dept_avg
FROM employees;
```

Now the window shrinks. SQL splits rows into groups by `department_id`, and computes the average **within each group**. The function runs once per partition.

```sql
-- Level 3: OVER(PARTITION BY ... ORDER BY ...) -- the window is ordered
SELECT
    employee_name,
    department_id,
    salary,
    SUM(salary) OVER(PARTITION BY department_id ORDER BY hire_date) AS running_total
FROM employees;
```

Adding `ORDER BY` inside `OVER()` changes the game entirely. Now the window is not just a static group -- it is an **ordered, growing window**. For each row, the function considers only the rows that came before it (including itself) within the partition. This is how you get running totals.

The key insight: `OVER()` controls **which rows** the function sees. Empty means all. `PARTITION BY` means grouped subsets. `ORDER BY` means ordered, cumulative subsets.

---

## PARTITION BY: GROUP BY That Does Not Collapse

`PARTITION BY` is conceptually almost identical to `GROUP BY`. Both split your data into groups. The difference is what happens to the rows.

- `GROUP BY` collapses all rows in a group into **one summary row**.
- `PARTITION BY` keeps **every row intact** and attaches the computed value as a new column.

```
GROUP BY                           PARTITION BY
+-------+-----------+              +-------+-----------+-----------+
| dept  | avg_salary|              | name  | dept      | avg_salary|
+-------+-----------+              +-------+-----------+-----------+
| Sales | 4800      |              | Alice | Sales     | 4800      |
| HR    | 5200      |              | Bob   | Sales     | 4800      |
| IT    | 6100      |              | Carol | HR        | 5200      |
+-------+-----------+              | Dave  | IT        | 6100      |
                                   | Eve   | HR        | 5200      |
                                   +-------+-----------+-----------+

Both split by department.          Same splits, but every row survives.
Only one row per group remains.    The aggregate value repeats on each row.
```

### Concrete example

```sql
SELECT
    employee_name,
    department_id,
    salary,
    COUNT(*) OVER(PARTITION BY department_id) AS employees_in_dept,
    AVG(salary) OVER(PARTITION BY department_id) AS avg_salary_in_dept,
    MAX(salary) OVER(PARTITION BY department_id) AS max_salary_in_dept
FROM employees;
```

Each row gets three new columns: the department headcount, the department average, and the department maximum. All computed independently. All without collapsing a single row.

You can partition by multiple columns too:

```sql
-- Average salary per department AND per year
SELECT
    employee_name,
    department_id,
    hire_year,
    salary,
    AVG(salary) OVER(PARTITION BY department_id, hire_year) AS dept_year_avg
FROM employees;
```

This splits data into groups where both `department_id` and `hire_year` match. Every unique combination becomes its own window.

---

## ORDER BY Inside OVER(): Defining Row Order Within the Window

When you add `ORDER BY` inside `OVER()`, you change how the window function sees rows. Instead of looking at an entire partition all at once, the function now processes rows **in order**, and for each row, it considers a **cumulative frame** -- all rows from the start of the partition up to and including the current row.

This is critical for two families of window functions:

1. **Running aggregations** -- cumulative sums, moving averages
2. **Ranking functions** -- row numbers, dense ranks

### Running totals

```sql
SELECT
    sale_date,
    amount,
    SUM(amount) OVER(ORDER BY sale_date) AS running_total
FROM sales;
```

```
+------------+--------+---------------+
| sale_date  | amount | running_total |
+------------+--------+---------------+
| 2025-01-01 |  100   |  100          |  <-- just row 1
| 2025-01-02 |  150   |  250          |  <-- rows 1 + 2
| 2025-01-03 |  200   |  450          |  <-- rows 1 + 2 + 3
| 2025-01-04 |  120   |  570          |  <-- rows 1 + 2 + 3 + 4
+------------+--------+---------------+

The window grows with each row. SUM sees an ever-larger set of rows.
```

Without `ORDER BY`, `SUM(amount) OVER()` would give the same grand total on every row. With `ORDER BY`, the sum **accumulates** row by row.

### Ranking

```sql
SELECT
    employee_name,
    salary,
    ROW_NUMBER() OVER(ORDER BY salary DESC) AS salary_rank
FROM employees;
```

Here, `ORDER BY` tells the ranking function: "sort employees by salary from highest to lowest, then assign numbers in that order." The highest salary gets rank 1, the second highest gets rank 2, and so on.

### Partitioned + Ordered

You can combine both:

```sql
-- Running total of sales, resetting per salesperson
SELECT
    salesperson,
    sale_date,
    amount,
    SUM(amount) OVER(PARTITION BY salesperson ORDER BY sale_date) AS person_running_total
FROM sales;
```

Each salesperson gets their own running total. The `PARTITION BY` creates separate windows; the `ORDER BY` makes each window cumulative.

---

## Ranking Functions: ROW_NUMBER, RANK, and DENSE_RANK

These three functions are often confused because they all assign numbers to rows. The difference only matters when there are **ties** -- when two or more rows have the same value. Let us use a concrete example.

### Sample data

```sql
SELECT employee_name, department_id, salary FROM employees ORDER BY salary DESC;
```

```
+-------+-------+--------+
| name  | dept  | salary |
+-------+-------+--------+
| Alice | Sales |  8000  |
| Bob   | IT    |  7500  |
| Carol | Sales |  7500  |   <-- tie with Bob
| Dave  | HR    |  7000  |
| Eve   | IT    |  6500  |
+-------+-------+--------+
```

Bob and Carol both earn 7500. Watch how each function handles this tie.

### ROW_NUMBER()

```sql
SELECT
    employee_name,
    salary,
    ROW_NUMBER() OVER(ORDER BY salary DESC) AS rn
FROM employees;
```

```
+-------+--------+----+
| name  | salary | rn |
+-------+--------+----+
| Alice |  8000  |  1 |
| Bob   |  7500  |  2 |   <-- arbitrarily picks Bob first
| Carol |  7500  |  3 |   <-- then Carol
| Dave  |  7000  |  4 |
| Eve   |  6500  |  5 |
+-------+--------+----+
```

`ROW_NUMBER()` never produces duplicates. When there is a tie, it picks one row arbitrarily. If you run the query again, Bob and Carol might swap. Use this when you need exactly N rows and do not care which tied row wins.

### RANK()

```sql
SELECT
    employee_name,
    salary,
    RANK() OVER(ORDER BY salary DESC) AS rnk
FROM employees;
```

```
+-------+--------+-----+
| name  | salary | rnk |
+-------+--------+-----+
| Alice |  8000  |  1  |
| Bob   |  7500  |  2  |  <-- tied
| Carol |  7500  |  2  |  <-- same rank
| Dave  |  7000  |  4  |  <-- SKIPS 3
| Eve   |  6500  |  5  |
+-------+--------+-----+
```

`RANK()` gives tied rows the same rank, then **skips** the next number. Think of it as: "If two people share 2nd place, there is no 3rd place -- the next person is 4th." This mirrors how Olympic medals work: if two athletes tie for silver, no one gets bronze.

### DENSE_RANK()

```sql
SELECT
    employee_name,
    salary,
    DENSE_RANK() OVER(ORDER BY salary DESC) AS drnk
FROM employees;
```

```
+-------+--------+------+
| name  | salary | drnk |
+-------+--------+------+
| Alice |  8000  |  1   |
| Bob   |  7500  |  2   |  <-- tied
| Carol |  7500  |  2   |  <-- same rank
| Dave  |  7000  |  3   |  <-- NO skip
| Eve   |  6500  |  4   |
+-------+--------+------+
```

`DENSE_RANK()` also gives tied rows the same rank, but does **not skip** the next number. After the two rank-2 rows, the next row gets rank 3. Use this when you want a continuous sequence of ranks.

### Summary table

| Function     | Ties      | Gaps? | Use when...                           |
|-------------|-----------|-------|---------------------------------------|
| ROW_NUMBER  | Broken    | No    | You need exactly N unique rows        |
| RANK        | Same rank | Yes   | You want "Olympic-style" ranking      |
| DENSE_RANK  | Same rank | No    | You want compact, gap-free ranks      |

You can also rank within partitions:

```sql
-- Rank employees by salary within each department
SELECT
    employee_name,
    department_id,
    salary,
    DENSE_RANK() OVER(PARTITION BY department_id ORDER BY salary DESC) AS dept_rank
FROM employees;
```

In Week 6, you will use `DENSE_RANK()` in dbt models to compute metrics like "each product's rank by revenue within its category this month."

---

## LAG and LEAD: Looking Behind and Ahead

`LAG()` and `LEAD()` let you access values from other rows **without a self-join**. They are your "look backward" and "look forward" functions within a window.

```
LAG(column, n)  -- grabs the value from n rows BEFORE the current row
LEAD(column, n) -- grabs the value from n rows AFTER the current row
```

### Classic use case: month-over-month comparison

You want to compare each month's sales to the previous month.

```sql
SELECT
    sale_month,
    monthly_revenue,
    LAG(monthly_revenue, 1) OVER(ORDER BY sale_month) AS prev_month_revenue,
    monthly_revenue - LAG(monthly_revenue, 1) OVER(ORDER BY sale_month) AS revenue_change
FROM monthly_sales;
```

```
+------------+-----------------+--------------------+----------------+
| sale_month | monthly_revenue | prev_month_revenue | revenue_change |
+------------+-----------------+--------------------+----------------+
| Jan        |  10000          | NULL               | NULL           |  <-- no previous month
| Feb        |  12000          | 10000              |  2000          |
| Mar        |  11000          | 12000              | -1000          |
| Apr        |  15000          | 11000              |  4000          |
+------------+-----------------+--------------------+----------------+
```

The first row has `NULL` for the lagged value because there is no row before it.

### Computing percentage change

```sql
SELECT
    sale_month,
    monthly_revenue,
    LAG(monthly_revenue, 1) OVER(ORDER BY sale_month) AS prev_month,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue, 1) OVER(ORDER BY sale_month))
        / LAG(monthly_revenue, 1) OVER(ORDER BY sale_month) * 100,
        1
    ) AS pct_change
FROM monthly_sales;
```

### Looking further back or ahead

```sql
-- Compare to the same month last year
LAG(monthly_revenue, 12) OVER(ORDER BY sale_month) AS year_ago_revenue

-- Peek at next month's planned revenue
LEAD(planned_revenue, 1) OVER(ORDER BY sale_month) AS next_month_planned
```

You can provide a default value instead of NULL:

```sql
LAG(monthly_revenue, 1, 0) OVER(ORDER BY sale_month) AS prev_month_revenue
-- First row gets 0 instead of NULL
```

In Week 6, `LAG()` is the standard tool in dbt pipelines for computing month-over-month growth rates, which are essential for business dashboards.

---

## Running Totals and Moving Averages

### Running totals

A running total (cumulative sum) is the simplest window function application:

```sql
SELECT
    sale_date,
    amount,
    SUM(amount) OVER(ORDER BY sale_date) AS running_total
FROM daily_sales;
```

```
+------------+--------+---------------+
| sale_date  | amount | running_total |
+------------+--------+---------------+
| Jan 1      |  100   |  100          |
| Jan 2      |  150   |  250          |
| Jan 3      |  200   |  450          |
| Jan 4      |  120   |  570          |
| Jan 5      |  180   |  750          |
+------------+--------+---------------+
```

Each row's `running_total` is the sum of all amounts from the first date through the current row's date.

### Moving averages

A moving average smooths out noise by averaging over a fixed-size window. The key difference from a running total: the window has a **fixed size** that slides forward, rather than growing indefinitely.

```sql
-- 3-day moving average
SELECT
    sale_date,
    amount,
    AVG(amount) OVER(
        ORDER BY sale_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3day
FROM daily_sales;
```

```
+------------+--------+-----------------+
| sale_date  | amount | moving_avg_3day |
+------------+--------+-----------------+
| Jan 1      |  100   |  100.0          |  <-- only 1 row available
| Jan 2      |  150   |  125.0          |  <-- avg(100, 150)
| Jan 3      |  200   |  150.0          |  <-- avg(100, 150, 200)
| Jan 4      |  120   |  156.7          |  <-- avg(150, 200, 120)
| Jan 5      |  180   |  166.7          |  <-- avg(200, 120, 180)
+------------+--------+-----------------+

The 3-row window slides forward one row at a time.
Old rows drop off as new rows enter.
```

Notice how Jan 4's moving average (156.7) uses only Jan 2, Jan 3, and Jan 4. Jan 1 has fallen out of the window. This is what makes it a "moving" average rather than a "running" average.

### Why this matters in pipelines

In Week 6, you will build dbt models that compute running metrics automatically. A typical pipeline might:
1. Aggregate daily sales into a fact table
2. Apply window functions to compute running totals and 7-day moving averages
3. Feed these smoothed metrics into a business dashboard

Window functions turn raw transactional data into trend-aware analytics with a single SQL statement.

---

## Frame Specification: Controlling the Window's Boundaries

The frame specification is the most powerful -- and most misunderstood -- part of window functions. It lets you define **exactly which rows** the function should consider, relative to the current row.

### The syntax

```sql
OVER(
    PARTITION BY ...
    ORDER BY ...
    frame_clause
)
```

The `frame_clause` has this structure:

```
ROWS BETWEEN <start> AND <end>
```

### The five boundary keywords

```
    UNBOUNDED PRECEDING    -- the very first row of the partition
    N PRECEDING            -- N rows before the current row
    CURRENT ROW            -- the current row itself
    N FOLLOWING            -- N rows after the current row
    UNBOUNDED FOLLOWING    -- the very last row of the partition
```

### Visual diagram

```
Partition of 10 rows, ordered by date. Current row is row 6 (marked with >>>).

Row  |  UNBOUNDED  |  2    | CURRENT |  2    |  UNBOUNDED
     | PRECEDING   |PREC.  |  ROW    |FOLLOW.| FOLLOWING
-----+-------------+-------+---------+-------+-------------
  1  |     IN      |  out  |   out   |  out  |    out
  2  |     IN      |  out  |   out   |  out  |    out
  3  |     IN      |  out  |   out   |  out  |    out
  4  |     IN      |  IN   |   out   |  out  |    out
  5  |     IN      |  IN   |   out   |  out  |    out
>>>> |     IN      |  IN   |   IN    |  out  |    out      <-- current row
  7  |     IN      |  out  |   out   |  IN   |    out
  8  |     IN      |  out  |   out   |  IN   |    out
  9  |     IN      |  out  |   out   |  out  |    out
 10  |     IN      |  out  |   out   |  out  |    out
```

### Common frame patterns

**Running total (from start to now):**
```sql
SUM(amount) OVER(ORDER BY sale_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
```
This is actually the **default** when you write `ORDER BY` without a frame. So `SUM(amount) OVER(ORDER BY sale_date)` means the same thing.

**Moving average (fixed-size window):**
```sql
AVG(amount) OVER(ORDER BY sale_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
```
A 3-row sliding window: 2 rows before + current row.

**Centered moving average:**
```sql
AVG(amount) OVER(ORDER BY sale_date ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING)
```
Averages the row before, current row, and row after. Useful for smoothing where you want the average to be "centered" on the current point.

**Running total from current row to end:**
```sql
SUM(amount) OVER(ORDER BY sale_date ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)
```
Each row shows "how much revenue remains from this point forward."

**Entire partition (all rows, no ordering effect):**
```sql
SUM(amount) OVER(PARTITION BY department_id)
```
No `ORDER BY` means the frame defaults to the entire partition.

### ROWS vs RANGE

There is a subtle distinction between `ROWS` and `RANGE`. `ROWS` counts physical rows. `RANGE` groups rows that have the same `ORDER BY` value together. For most practical purposes, use `ROWS` -- it is more predictable and intuitive.

---

## The "Top-N per Group" Pattern

This is the single most common window function pattern you will use in practice. The question always sounds something like:

> "Find the top 3 highest-paid employees in each department."

Or:

> "Find the top 5 products by revenue in each category."

Or:

> "Find the most recent order for each customer."

All of these follow the exact same template.

### Step-by-step walkthrough

**Step 1: Write the table you are working with.**

```sql
SELECT employee_name, department_id, salary FROM employees;
```

```
+-------+-------+--------+
| name  | dept  | salary |
+-------+-------+--------+
| Alice | Sales |  8000  |
| Bob   | Sales |  7500  |
| Carol | Sales |  7200  |
| Dave  | Sales |  6800  |
| Eve   | Sales |  6500  |
| Frank | IT    |  9000  |
| Grace | IT    |  8500  |
| Hank  | IT    |  8000  |
| Ivy   | IT    |  7000  |
+-------+-------+--------+
```

**Step 2: Add a row number, partitioned by group, ordered by the ranking criterion.**

```sql
SELECT
    employee_name,
    department_id,
    salary,
    ROW_NUMBER() OVER(PARTITION BY department_id ORDER BY salary DESC) AS rn
FROM employees;
```

```
+-------+-------+--------+----+
| name  | dept  | salary | rn |
+-------+-------+--------+----+
| Alice | Sales |  8000  |  1 |  <-- highest in Sales
| Bob   | Sales |  7500  |  2 |
| Carol | Sales |  7200  |  3 |
| Dave  | Sales |  6800  |  4 |
| Eve   | Sales |  6500  |  5 |
| Frank | IT    |  9000  |  1 |  <-- highest in IT (rn restarts!)
| Grace | IT    |  8500  |  2 |
| Hank  | IT    |  8000  |  3 |
| Ivy   | IT    |  7000  |  4 |
+-------+-------+--------+----+

Notice: rn starts at 1 for each department. PARTITION BY resets the counter.
```

**Step 3: Wrap in a CTE and filter.**

You cannot use `rn` in a `WHERE` clause in the same query -- SQL evaluates `WHERE` before window functions. So you wrap the query in a CTE (or subquery) and filter in the outer query.

```sql
WITH ranked AS (
    SELECT
        employee_name,
        department_id,
        salary,
        ROW_NUMBER() OVER(PARTITION BY department_id ORDER BY salary DESC) AS rn
    FROM employees
)
SELECT employee_name, department_id, salary
FROM ranked
WHERE rn <= 3;
```

```
+-------+-------+--------+
| name  | dept  | salary |
+-------+-------+--------+
| Alice | Sales |  8000  |  <-- Top 3 in Sales
| Bob   | Sales |  7500  |
| Carol | Sales |  7200  |
| Frank | IT    |  9000  |  <-- Top 3 in IT
| Grace | IT    |  8500  |
| Hank  | IT    |  8000  |
+-------+-------+--------+
```

### Why ROW_NUMBER and not RANK?

If two employees in the same department earn exactly the same salary, `ROW_NUMBER()` arbitrarily picks one. If you want **all** tied employees to appear (which might give you more than 3 results), use `DENSE_RANK()` instead. The template is identical -- just swap the function.

### The universal template

Memorize this pattern. It solves dozens of real-world questions:

```sql
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER(PARTITION BY <group_column> ORDER BY <ranking_column> DESC) AS rn
    FROM <your_table>
)
SELECT *
FROM ranked
WHERE rn <= <N>;
```

Replace `<group_column>`, `<ranking_column>`, and `<N>` with your specifics. In Week 6, you will use this exact pattern in dbt models to surface "top performers per category" as reusable data models that feed dashboards and reports.
