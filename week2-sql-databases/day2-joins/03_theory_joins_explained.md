# Day 2: JOINs Explained

## Connecting Data from Multiple Tables

In Day 1, you queried a single table: `employees`. But the real power of relational databases comes from **combining data across multiple tables**. That's what JOINs do.

If you used `pd.merge()` in pandas during Week 1, you already know this concept. SQL JOINs are the same idea — but built into the database engine itself, making them faster and more expressive.

---

## Why Do JOINs Exist?

### The Normalization Principle

Data is split across tables to **avoid duplication**. Consider this example:

**Without normalization (bad):**
```
employees_bad table:
┌────────┬──────────┬───────────────┬─────────────┬──────────┐
│ emp_id │   name   │  dept_name    │ dept_location│ salary   │
├────────┼──────────┼───────────────┼─────────────┼──────────┤
│   1    │ Alice    │ Engineering   │ Building A  │ 145000   │
│   2    │ Bob      │ Engineering   │ Building A  │ 125000   │
│   3    │ Carol    │ Engineering   │ Building A  │  95000   │
│   9    │ Iris     │ HR            │ Building B  │ 115000   │
│  10    │ Jack     │ HR            │ Building B  │  85000   │
└────────┴──────────┴───────────────┴─────────────┴──────────┘
```

See the problem? "Engineering, Building A" is repeated for every engineer. If the department moves to Building X, you must update hundreds of rows. If you miss one, your data is inconsistent.

**With normalization (good):**
```
employees table:               departments table:
┌────────┬───────┬──────────┐  ┌──────────┬───────────────┬─────────────┐
│ emp_id │ name  │ dept_id  │  │ dept_id  │  dept_name    │ location    │
├────────┼───────┼──────────┤  ├──────────┼───────────────┼─────────────┤
│   1    │ Alice │    1     │  │    1     │ Engineering   │ Building A  │
│   2    │ Bob   │    1     │  │    2     │ HR            │ Building B  │
│   3    │ Carol │    1     │  │    3     │ Finance       │ Building C  │
│   9    │ Iris  │    2     │  └──────────┴───────────────┴─────────────┘
│  10    │ Jack  │    2     │
└────────┴───────┴──────────┘
```

Each piece of information lives in **one place only**. When the department moves, you update one row in `departments`. Every employee automatically reflects the change through the relationship.

**But now you have a problem:** When you want to see "Alice Chen and her department name," the data is split. You need to **reconnect** the tables. That's what JOINs do.

---

## The ON Clause: The Heart of Every JOIN

Every JOIN needs an **ON clause** — the condition that determines which rows match.

```sql
SELECT *
FROM employees
JOIN departments ON employees.department_id = departments.dept_id;
```

`ON employees.department_id = departments.dept_id` means: "Match each employee's `department_id` to the corresponding `dept_id` in the departments table."

Usually, this is a foreign key pointing to a primary key. But you can join on any condition (dates, names, computed values — anything that makes sense).

---

## Visual Explanation of Each JOIN Type

Let's use two small tables to demonstrate each join type.

### Our Example Tables

```
employees                       departments
┌─────────┬──────────┐          ┌──────────┬─────────────┐
│ emp_id  │ dept_id  │          │ dept_id  │  dept_name  │
├─────────┼──────────┤          ├──────────┼─────────────┤
│   1     │    1     │          │    1     │ Engineering │
│   2     │    1     │          │    2     │    HR       │
│   3     │    2     │          │    3     │   Finance   │
│   4     │   NULL   │          └──────────┴─────────────┘
│   5     │    99    │  (invalid dept_id)
└─────────┴──────────┘
```

Note:
- Employee 4 has `dept_id = NULL` (unassigned)
- Employee 5 has `dept_id = 99` (no matching department exists)

---

### 1. INNER JOIN

**Definition:** Only rows where the key matches in **BOTH** tables.

**Plain English:** "Give me employees who have a valid department."

```
Result of: employees INNER JOIN departments ON employees.dept_id = departments.dept_id

┌─────────┬──────────┬──────────┬─────────────┐
│ emp_id  │ dept_id  │ dept_id  │  dept_name  │
├─────────┼──────────┼──────────┼─────────────┤
│   1     │    1     │    1     │ Engineering │  ← matched
│   2     │    1     │    1     │ Engineering │  ← matched
│   3     │    2     │    2     │    HR       │  ← matched
└─────────┴──────────┴──────────┴─────────────┘
```

**What happened to each employee?**
- Employee 1 (dept 1) → Matched Engineering ✓
- Employee 2 (dept 1) → Matched Engineering ✓
- Employee 3 (dept 2) → Matched HR ✓
- Employee 4 (NULL) → **DISAPPEARED** (NULL doesn't match anything)
- Employee 5 (dept 99) → **DISAPPEARED** (no department 99 exists)

**Key insight:** INNER JOIN can **lose rows** if they don't have a match. This is the #1 beginner mistake — joining and not realizing you silently lost data.

---

### 2. LEFT JOIN (Most Commonly Used)

**Definition:** ALL rows from the left table (first one), with matching rows from the right table. Where no match exists, right-side columns are NULL.

**Plain English:** "Give me ALL employees, and their department name if they have one."

```
Result of: employees LEFT JOIN departments ON employees.dept_id = departments.dept_id

┌─────────┬──────────┬──────────┬─────────────┐
│ emp_id  │ dept_id  │ dept_id  │  dept_name  │
├─────────┼──────────┼──────────┼─────────────┤
│   1     │    1     │    1     │ Engineering │  ← matched
│   2     │    1     │    1     │ Engineering │  ← matched
│   3     │    2     │    2     │    HR       │  ← matched
│   4     │   NULL   │   NULL   │    NULL     │  ← no match, NULLs
│   5     │   99     │   NULL   │    NULL     │  ← no match, NULLs
└─────────┴──────────┴──────────┴─────────────┘
```

**What happened?**
- Employees 1, 2, 3: Matched normally (same as INNER JOIN)
- Employee 4: Kept in the result, but department columns are NULL
- Employee 5: Kept in the result, but department columns are NULL

**Why is LEFT JOIN the default in real work?** Because you rarely want to silently lose data. If an employee doesn't have a department yet (maybe they're new), you still want to see them in your report.

---

### 3. RIGHT JOIN

**Definition:** Mirror of LEFT JOIN — ALL rows from the right table, matching rows from the left.

**Plain English:** "Give me ALL departments, and their employees if they have any."

```
Result of: employees RIGHT JOIN departments ON employees.dept_id = departments.dept_id

┌─────────┬──────────┬──────────┬─────────────┐
│ emp_id  │ dept_id  │ dept_id  │  dept_name  │
├─────────┼──────────┼──────────┼─────────────┤
│   1     │    1     │    1     │ Engineering │  ← has employees
│   2     │    1     │    1     │ Engineering │  ← has employees
│   3     │    2     │    2     │    HR       │  ← has employees
│  NULL   │   NULL   │    3     │   Finance   │  ← no employees, NULLs on left
└─────────┴──────────┴──────────┴─────────────┘
```

**Practical tip:** RIGHT JOIN is rarely used in practice. Just swap the table order and use LEFT JOIN instead. They produce identical results:

```sql
-- These two queries produce the SAME result:
employees RIGHT JOIN departments ON ...
departments LEFT JOIN employees ON ...
```

---

### 4. FULL OUTER JOIN

**Definition:** ALL rows from BOTH tables. NULLs on either side where no match exists.

**Plain English:** "Give me everything — matched or unmatched employees AND matched or unmatched departments."

```
Result of: employees FULL OUTER JOIN departments ON employees.dept_id = departments.dept_id

┌─────────┬──────────┬──────────┬─────────────┐
│ emp_id  │ dept_id  │ dept_id  │  dept_name  │
├─────────┼──────────┼──────────┼─────────────┤
│   1     │    1     │    1     │ Engineering │  ← matched
│   2     │    1     │    1     │ Engineering │  ← matched
│   3     │    2     │    2     │    HR       │  ← matched
│   4     │   NULL   │   NULL   │    NULL     │  ← employee with no dept
│   5     │   99     │   NULL   │    NULL     │  ← employee with invalid dept
│  NULL   │   NULL   │    3     │   Finance   │  ← department with no employees
└─────────┴──────────┴──────────┴─────────────┘
```

**Use case:** Finding orphan records on both sides at once — employees without departments AND departments without employees.

---

### 5. CROSS JOIN

**Definition:** Every row from table A combined with every row from table B.

**Plain English:** "All possible combinations."

```
If employees has 50 rows and departments has 6 rows:
Result = 50 × 6 = 300 rows
```

**Warning:** Almost never what you want. If you accidentally forget the ON clause in a JOIN, PostgreSQL does a CROSS JOIN and returns a massive result set. This is a common beginner mistake.

---

### 6. Self-Join

**Definition:** Joining a table to itself.

**Plain English:** "Find each employee and their manager" — where both the employee and the manager are rows in the same `employees` table.

```sql
SELECT 
    e.first_name AS employee_name,
    m.first_name AS manager_name
FROM employees e
JOIN employees m ON e.manager_id = m.emp_id;
```

**Why aliases are mandatory:** When the same table appears twice, you must use aliases (`e` for employee, `m` for manager) so PostgreSQL knows which instance you're referring to.

**Result:**
```
┌─────────────────┬────────────────┐
│ employee_name   │  manager_name  │
├─────────────────┼────────────────┤
│ Bob Martinez    │   Alice Chen   │  (Bob's manager is Alice)
│ Carol Johnson   │   Bob Martinez │  (Carol's manager is Bob)
│ ...             │   ...          │
└─────────────────┴────────────────┘
```

Employees with `manager_id = NULL` (the directors) won't appear because NULL doesn't match any emp_id in an INNER JOIN. Use LEFT JOIN to include them.

---

## Multi-Table JOINs

Real analytical queries often join 3, 4, or more tables:

```sql
SELECT e.first_name, d.dept_name, s.quantity, p.product_name
FROM employees e
JOIN departments d ON e.department_id = d.dept_id
JOIN sales s ON e.emp_id = s.employee_id
JOIN products p ON s.product_id = p.product_id;
```

**Build these step by step:**
1. Join 2 tables, verify the result
2. Add the 3rd table, verify
3. Add the 4th table, verify

Each JOIN adds more context to your result.

---

## Common JOIN Mistakes

### Mistake 1: Forgetting the ON Clause

```sql
-- WRONG: This is a CROSS JOIN (accidental!)
SELECT * FROM employees JOIN departments;

-- RIGHT: Include the ON condition
SELECT * FROM employees JOIN departments ON employees.dept_id = departments.dept_id;
```

Without ON, you get every employee × every department (50 × 6 = 300 rows). If your tables are large, this can freeze your database.

### Mistake 2: Joining on the Wrong Columns

```sql
-- WRONG: Joining on names instead of IDs
SELECT * FROM employees 
JOIN departments ON employees.first_name = departments.dept_name;

-- This produces nonsense! Always join on the relationship (foreign key → primary key).
```

### Mistake 3: Not Understanding NULLs in LEFT JOIN

```sql
-- WRONG: Trying to filter NULLs from the LEFT side in WHERE
SELECT e.*, d.dept_name
FROM employees e
LEFT JOIN departments d ON e.department_id = d.dept_id
WHERE d.dept_name IS NULL;  -- This converts LEFT JOIN to INNER JOIN behavior!
```

When you add `WHERE d.dept_name IS NULL`, you're saying "only show me unmatched employees." This is actually a useful pattern for finding orphans, but it defeats the purpose of a LEFT JOIN if you wanted all employees.

---

## Connection to pandas (Week 1)

In Week 1, you used `pd.merge()`:

```python
# pandas
pd.merge(employees, departments, on='dept_id', how='inner')
```

The SQL equivalent:

```sql
-- SQL
SELECT * FROM employees
INNER JOIN departments ON employees.dept_id = departments.dept_id;
```

The `how` parameter maps directly:
- `how='inner'` → INNER JOIN
- `how='left'` → LEFT JOIN
- `how='right'` → RIGHT JOIN
- `how='outer'` → FULL OUTER JOIN

SQL JOINs are often more readable because the ON condition is explicit — you see exactly which columns are being matched.

---

## Forward Connection

> **Looking ahead:** In Week 4, you'll build ETL pipelines that JOIN data from multiple sources — a CRM table, a billing table, and a support ticket table. The JOINs you learn today are the foundation of those pipelines. In Week 6, dbt models are essentially chains of JOINs wrapped in CTEs. Master JOINs now, and those later modules will feel natural.

---

## What's Next?

Open `04_joins_practice.ipynb` to practice every join type with real data. You'll see INNER JOIN lose rows, LEFT JOIN preserve them, and self-joins reveal the manager hierarchy.
