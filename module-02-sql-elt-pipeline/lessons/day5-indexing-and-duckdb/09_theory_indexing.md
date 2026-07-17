# Theory: Understanding Database Indexing

## Why Are My Queries So Slow?

Imagine you have a `sales` table with 1,000,000 rows. You run this query:

```sql
SELECT * FROM sales WHERE product_name = 'Barbie';
```

Without an index, PostgreSQL has only **one way** to answer this question: **read every single row**, one by one, and check if `product_name` equals `'Barbie'`. This is called a **Sequential Scan** (shown as `Seq Scan` in query plans).

It is like having a 1000-page book and needing to find every mention of "PostgreSQL". Without an index, you must read **every single page** from start to finish. That could take hours.

```
Sequential Scan (no index):
  Row 1:    product_name = 'Lego Set'      --> not a match, skip
  Row 2:    product_name = 'UNO Cards'      --> not a match, skip
  Row 3:    product_name = 'Play-Doh'       --> not a match, skip
  Row 4:    product_name = 'Barbie'         --> match!
  Row 5:    product_name = 'Hot Wheels'     --> not a match, skip
  ...
  Row 1000000: product_name = 'Nerf Gun'    --> not a match, skip
```

If the table has 1 million rows, PostgreSQL may need to check all 1 million. On a large table, this can take **seconds or even minutes**.

---

## What Is an Index?

An **index** is a separate data structure that maps column values to the physical locations of rows in the table. It lets PostgreSQL jump directly to the rows it needs, instead of reading everything.

Think of the **index at the back of a textbook**:

```
Book Index:
  PostgreSQL ............ 47, 112, 389
  Index ................. 55, 112, 203, 401
  Query ................. 15, 47, 89, 234
  Table ................. 22, 89, 156
```

When you want to find "PostgreSQL", you look it up in the index and immediately know it is on pages 47, 112, and 389. You go **directly** to those pages. You do not need to read pages 1-46, 48-111, or 113-388.

The same idea applies to a database:

```sql
-- Create an index on the product_name column
CREATE INDEX idx_sales_product ON sales (product_name);
```

Now when you query:

```sql
SELECT * FROM sales WHERE product_name = 'Barbie';
```

PostgreSQL:

1. Looks up `'Barbie'` in the index.
2. The index tells it exactly which rows contain `'Barbie'`.
3. It fetches only those rows directly.

Instead of scanning 1,000,000 rows, it might read **3 rows**. That is the difference between a query taking 2 seconds and taking 2 milliseconds.

---

## The B-tree Index (PostgreSQL Default)

The default index type in PostgreSQL is the **B-tree** (balanced tree). It is the best general-purpose index for most queries.

### How a B-tree Works

A B-tree stores values in a **sorted, hierarchical tree structure**. At each level, PostgreSQL compares the search value and decides whether to go left or right -- like a binary search.

Here is a simplified B-tree containing 15 salary values from our employees table:

```
                        [Root Node]
                     [55000 | 72000 | 88000]
                           /    |    \
                          /     |     \
              [Left]     /      |      \     [Right]
        [38000|45000]   /  [60000|68000]  \   [92000|98000]
            /    \     /       |    \      \       |    \
           /      \   /        |     \      \      |     \
  [35k|38k] [42k|45k] [55k|60k] [65k|68k] [75k|80k] [85k|88k] [92k|95k] [98k|105k]
```

### Finding a Value: salary = 85000

Let us trace how PostgreSQL finds `salary = 85000`:

```
Step 1: Start at Root [55000 | 72000 | 88000]
        85000 > 72000 AND 85000 < 88000  --> go RIGHT

Step 2: Node [75000 | 80000]
        85000 > 80000  --> go RIGHT

Step 3: Leaf node [85000 | 88000]
        Found 85000!  --> fetch the matching row(s)
```

Only **3 steps** to find the value in a tree of 15 values.

Now imagine a table with **1,000,000 rows**. A B-tree is typically 3-4 levels deep even for millions of rows. PostgreSQL finds the answer in **3-4 steps** instead of scanning 1,000,000 rows. That is the power of a B-tree index.

```
WITHOUT index:  1,000,000 row reads  --> ~2000 ms
WITH index:     3-4 tree steps        --> ~2 ms
```

### Visual comparison

```
Sequential scan (no index):           B-tree index scan:

  [row1] [row2] [row3] [row4] ...      [Root]
    |      |      |      |               /  \
   check  check  check  check         [Left] [Right]
    |      |      |      |               |      |
   skip   skip   skip   FOUND!        check  check
                                        |      |
                                      skip   FOUND!

  Reads: ~500,000 on average           Reads: ~3-4 steps
```

---

## When Should You Create an Index?

### Good candidates for indexes

| Situation | Why | Example |
|-----------|-----|---------|
| **Columns in WHERE clauses you query often** | Index lets PostgreSQL jump to matching rows | `WHERE customer_id = 42` |
| **Columns in JOIN conditions (especially foreign keys)** | Joins repeatedly look up matching values | `JOIN orders ON customers.id = orders.customer_id` |
| **Columns in ORDER BY** | B-tree stores values sorted, so results are already in order | `ORDER BY created_at DESC` |
| **Columns with many distinct values (high cardinality)** | Index is most effective when it narrows down significantly | `WHERE email = 'user@example.com'` |

### When NOT to create an index

| Situation | Why avoid it |
|-----------|-------------|
| **Columns rarely used in WHERE, JOIN, or ORDER BY** | Index costs disk space and slows writes, but provides no benefit |
| **Very small tables (under ~1000 rows)** | Sequential scan is fast enough; index overhead is not worth it |
| **Columns with very few distinct values (low cardinality)** | A boolean column (`is_active`) only has `true`/`false`. The index would match ~50% of rows each time -- almost as slow as reading the whole table. PostgreSQL often ignores such indexes anyway |

### Practical example

```sql
-- GOOD: customer_id appears in WHERE clauses frequently
CREATE INDEX idx_orders_customer ON orders (customer_id);

-- GOOD: created_at appears in ORDER BY and range queries
CREATE INDEX idx_orders_created ON orders (created_at);

-- BAD: status only has 3 values ('pending', 'shipped', 'delivered')
-- Index helps little; PostgreSQL likely ignores it
CREATE INDEX idx_orders_status ON orders (status);  -- probably not useful

-- BAD: tiny lookup table with only 50 rows
CREATE INDEX idx_countries_name ON countries (name);  -- not worth it
```

---

## Composite (Multi-Column) Indexes

A composite index covers **multiple columns** in a specific order:

```sql
CREATE INDEX idx_employees_dept_salary ON employees (department_id, salary);
```

### The Phone Book Analogy

A phone book is sorted by **last name, then first name**:

```
Smith, Alice ...... 555-0101
Smith, Bob ........ 555-0202
Smith, Charlie .... 555-0303
Jones, Alice ...... 555-0404
Jones, David ...... 555-0505
```

You can easily:
- Look up **all Smiths** (last name only) -- they are grouped together.
- Look up **"Smith, Bob"** (both last and first name) -- exact match.

But you **cannot** easily:
- Look up **everyone named "Bob"** (first name only) -- Bobs are scattered throughout the book.

### How composite indexes work

An index on `(department_id, salary)` helps these queries:

```sql
-- Works great: uses the index (leftmost column)
SELECT * FROM employees WHERE department_id = 5;

-- Works great: uses the index (both columns)
SELECT * FROM employees WHERE department_id = 5 AND salary > 70000;

-- Works OK: uses the index partially (only department_id)
SELECT * FROM employees WHERE department_id = 5 ORDER BY salary;
```

But it does **NOT** help this query:

```sql
-- Does NOT use the index: salary alone (skips department_id)
SELECT * FROM employees WHERE salary > 70000;  -- sequential scan!
```

The rule: **a composite index on (A, B) helps queries filtering by A, or by A AND B, but NOT by B alone.**

```
Index: (department_id, salary)

  dept_id | salary
  --------+--------
     1    | 45000
     1    | 52000
     1    | 61000   <-- all dept 1 grouped together, sorted by salary
     2    | 48000
     2    | 55000
     2    | 72000   <-- all dept 2 grouped together, sorted by salary
     3    | 50000
     3    | 67000
     3    | 85000   <-- all dept 3 grouped together, sorted by salary

Query: WHERE department_id = 2           --> jumps to dept 2 block instantly
Query: WHERE department_id = 2 AND salary > 60000  --> finds dept 2, then uses salary ordering
Query: WHERE salary > 70000              --> must scan everything; 72000, 85000, etc. are scattered
```

### Which column should come first?

Put the **more selective** column first (the one that narrows down results more), or the column that appears more often in your queries.

```sql
-- If you often filter by department AND then by salary:
CREATE INDEX idx_emp_dept_salary ON employees (department_id, salary);

-- If you often filter by salary range regardless of department:
-- (rare in practice, but if you do)
CREATE INDEX idx_emp_salary_dept ON employees (salary, department_id);
```

---

## EXPLAIN ANALYZE -- Seeing How PostgreSQL Executes Your Query

`EXPLAIN ANALYZE` is PostgreSQL's built-in tool for understanding **how** a query is actually executed. It shows you the execution plan and the real timing.

```sql
EXPLAIN ANALYZE SELECT * FROM sales WHERE product_name = 'Barbie';
```

### Example output (WITHOUT an index)

```
                                                     QUERY PLAN
---------------------------------------------------------------------------------------------------------------------
 Seq Scan on sales  (cost=0.00..22981.00 rows=4 width=128) (actual time=0.028..156.234 rows=4 loops=1)
   Filter: (product_name = 'Barbie'::text)
   Rows Removed by Filter: 999996
 Planning Time: 0.142 ms
 Execution Time: 156.312 ms
```

Let us break down every part:

```
Seq Scan on sales
^^^^^^^^^^^^^^^^^^^
Seq Scan = Sequential Scan
PostgreSQL is reading EVERY row in the sales table, one by one.
No index is being used. This is slow for large tables.

(cost=0.00..22981.00 rows=4 width=128)
 ^^^^^^^^^^^^^^^^^^ ^^^^^^ ^^^^^^^^^^^
 |                  |      |
 |                  |      +-- width: each row is ~128 bytes
 |                  +-- rows: PostgreSQL estimates 4 rows will match
 +-- cost: estimated "units of work"
     0.00 = startup cost (before first row)
     22981.00 = total cost to scan the entire table
     (lower is better, but these are relative units, not milliseconds)

(actual time=0.028..156.234 rows=4 loops=1)
 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 actual time = REAL measured time in milliseconds
   0.028 = time before first row returned (startup)
   156.234 = total time to finish the scan
 rows=4 = actually found 4 matching rows
 loops=1 = this step ran once

Filter: (product_name = 'Barbie'::text)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is the condition PostgreSQL checked for every row.

Rows Removed by Filter: 999996
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PostgreSQL read 1,000,000 rows and threw away 999,996 of them.
Only 4 rows matched. This is very inefficient.

Planning Time: 0.142 ms
^^^^^^^^^^^^^^^^^^^^^^^
Time PostgreSQL spent figuring out the best way to run this query.
(Usually very fast, under 1 ms.)

Execution Time: 156.312 ms
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Total real time the query took to run.
156 milliseconds for a simple lookup -- too slow!
```

### Same query AFTER creating an index

```sql
CREATE INDEX idx_sales_product ON sales (product_name);

EXPLAIN ANALYZE SELECT * FROM sales WHERE product_name = 'Barbie';
```

```
                                                             QUERY PLAN
------------------------------------------------------------------------------------------------------------------------------
 Index Scan using idx_sales_product on sales  (cost=0.42..8.44 rows=4 width=128) (actual time=0.035..0.052 rows=4 loops=1)
   Index Cond: (product_name = 'Barbie'::text)
 Planning Time: 0.189 ms
 Execution Time: 0.089 ms
```

Notice the differences:

| Aspect | Without Index | With Index | Improvement |
|--------|--------------|------------|-------------|
| **Scan type** | `Seq Scan` | `Index Scan` | Uses the index |
| **Estimated cost** | 0..22981 | 0.42..8.44 | ~2700x lower |
| **Actual time** | 0.028..156.234 ms | 0.035..0.052 ms | ~3000x faster |
| **Rows Removed by Filter** | 999,996 | (not shown -- none!) | No wasted reads |
| **Execution Time** | 156.312 ms | 0.089 ms | ~1756x faster |

### Key terms you will see in EXPLAIN ANALYZE output

| Term | Meaning | Good or Bad? |
|------|---------|--------------|
| **Seq Scan** | Full table scan, reads every row | Slow on large tables |
| **Index Scan** | Uses an index to find specific rows | Fast |
| **Bitmap Index Scan** | Uses index to build a bitmap of matching rows, then fetches them. Used when many rows match (more than a few, but fewer than the whole table) | Still good -- better than Seq Scan |
| **Index Only Scan** | All needed columns are in the index itself. PostgreSQL never needs to visit the actual table rows | Fastest possible |
| **cost=A..B** | Estimated work units. A = startup cost, B = total cost | Lower is better |
| **actual time=A..B** | Real time in milliseconds | Lower is better |
| **rows=N** | Number of rows this step processed | Depends on query |
| **loops=N** | How many times this step ran | Usually 1 |
| **Rows Removed by Filter** | Rows read but discarded | High number = inefficient |

### Example with Bitmap Index Scan

```sql
EXPLAIN ANALYZE SELECT * FROM employees WHERE department_id IN (1, 2, 3, 4, 5);
```

```
                                                           QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on employees  (cost=12.50..156.78 rows=500 width=96) (actual time=0.45..2.31 rows=512 loops=1)
   Recheck Cond: (department_id = ANY ('{1,2,3,4,5}'::integer[]))
   Heap Blocks: exact=128
   ->  Bitmap Index Scan on idx_employees_dept  (cost=0.00..12.38 rows=500 width=0) (actual time=0.38..0.38 rows=512 loops=1)
         Index Cond: (department_id = ANY ('{1,2,3,4,5}'::integer[]))
 Planning Time: 0.201 ms
 Execution Time: 2.567 ms
```

A **Bitmap Index Scan** works in two phases:

1. **Phase 1** -- Bitmap Index Scan: PostgreSQL uses the index to build a "bitmap" (a list of which rows match). Think of it as marking all matching pages with a sticky note.
2. **Phase 2** -- Bitmap Heap Scan: PostgreSQL goes through the actual table and fetches only the marked rows.

This is used when **many rows match** -- too many for individual index lookups, but too few to justify reading the entire table.

### Example with Index Only Scan

```sql
-- If we have an index on (department_id, salary)
EXPLAIN ANALYZE SELECT department_id, salary FROM employees WHERE department_id = 3;
```

```
                                                              QUERY PLAN
-------------------------------------------------------------------------------------------------------------------------------
 Index Only Scan using idx_emp_dept_salary on employees  (cost=0.29..4.33 rows=15 width=12) (actual time=0.018..0.025 rows=15 loops=1)
   Index Cond: (department_id = 3)
   Heap Fetches: 0
 Planning Time: 0.167 ms
 Execution Time: 0.041 ms
```

**Index Only Scan** means PostgreSQL found everything it needed inside the index itself -- it never had to visit the actual table. This is the **fastest** type of scan. Note `Heap Fetches: 0` -- zero trips to the actual table.

---

## Why Not Index Everything?

If indexes make queries faster, why not just index every column?

### Indexes have costs

**1. Disk space**

Every index is a separate data structure stored on disk. A large index can be as big as the table itself.

```sql
-- Check the size of your indexes
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

```
       indexname        | index_size
------------------------+------------
 idx_sales_product      | 48 MB
 idx_sales_customer     | 32 MB
 idx_employees_dept     | 12 MB
 idx_orders_date        | 8 MB
```

**2. Slower writes (INSERT, UPDATE, DELETE)**

Every time you **insert** a row, PostgreSQL must also add that row's values to every relevant index. Every **update** to an indexed column requires updating the index. Every **delete** requires removing the entry from the index.

```
Without indexes:
  INSERT --> Write 1 row to the table.  Done.

With 5 indexes:
  INSERT --> Write 1 row to the table
          --> Update index 1
          --> Update index 2
          --> Update index 3
          --> Update index 4
          --> Update index 5
          Done. (6 writes instead of 1!)
```

```
INSERT with 0 indexes:  ~1 ms
INSERT with 3 indexes:  ~3 ms
INSERT with 8 indexes:  ~8 ms
```

For a data pipeline inserting 100,000 rows, this difference matters:

```
100,000 rows x 1 ms  = 100 seconds
100,000 rows x 8 ms  = 800 seconds (13 minutes)
```

### The right approach: balance

Create indexes on columns that are:

- **Queried frequently** in WHERE, JOIN, or ORDER BY.
- **Selective enough** to narrow down results significantly.
- **Not already covered** by an existing index.

Avoid indexes on:

- Columns only used for INSERTs (data loading).
- Very small tables.
- Columns with very few distinct values (boolean, status enums with 2-3 values).

---

## Putting It All Together

### Practical workflow

```sql
-- Step 1: Write your query
SELECT * FROM sales WHERE product_name = 'Barbie';

-- Step 2: Check how it executes
EXPLAIN ANALYZE SELECT * FROM sales WHERE product_name = 'Barbie';
-- If you see "Seq Scan" on a large table, consider an index

-- Step 3: Create the index
CREATE INDEX idx_sales_product ON sales (product_name);

-- Step 4: Verify the improvement
EXPLAIN ANALYZE SELECT * FROM sales WHERE product_name = 'Barbie';
-- Should now show "Index Scan" with much lower times
```

### Common indexing patterns in practice

```sql
-- Foreign keys (almost always worth indexing)
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
CREATE INDEX idx_order_items_order_id ON order_items (order_id);

-- Date columns (for range queries and sorting)
CREATE INDEX idx_sales_date ON sales (sale_date);

-- Composite index for common query patterns
CREATE INDEX idx_sales_product_date ON sales (product_name, sale_date);

-- Unique index (also enforces uniqueness)
CREATE UNIQUE INDEX idx_users_email ON users (email);
```

---

## Forward Connection: Indexing in ETL Pipelines

In **Week 4**, when you build ETL (Extract, Transform, Load) pipelines, you will create and populate tables with raw data. After loading, you will add indexes to frequently-queried columns to speed up downstream transformations and reporting queries.

A typical ETL pattern:

```sql
-- Step 1: Create the table
CREATE TABLE raw_sales (
    sale_id      SERIAL PRIMARY KEY,
    product_name VARCHAR(100),
    sale_date    DATE,
    amount       NUMERIC(10, 2)
);

-- Step 2: Load data (faster WITHOUT indexes during bulk insert)
COPY raw_sales (product_name, sale_date, amount)
FROM '/path/to/sales_data.csv'
DELIMITER ',' CSV HEADER;

-- Step 3: Add indexes AFTER loading (for query performance)
CREATE INDEX idx_raw_sales_product ON raw_sales (product_name);
CREATE INDEX idx_raw_sales_date ON raw_sales (sale_date);

-- Step 4: Run your analytical queries (fast!)
EXPLAIN ANALYZE
SELECT product_name, SUM(amount) AS total_sales
FROM raw_sales
WHERE sale_date >= '2025-01-01'
GROUP BY product_name;
```

By loading data first and adding indexes afterward, you avoid the overhead of updating indexes during bulk inserts. Then, your analytical queries and dashboard reports run efficiently against the indexed columns.
