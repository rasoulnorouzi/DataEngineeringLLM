-- Week 2 SQL Curriculum: Company Dataset Initialization
-- This script creates a realistic company dataset for learning SQL

CREATE SCHEMA IF NOT EXISTS company;
SET search_path TO company, public;

-- ============================================================
-- DEPARTMENTS TABLE
-- 6 departments across different locations
-- ============================================================
CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    budget NUMERIC(12, 2)
);

INSERT INTO departments (dept_name, location, budget) VALUES
('Engineering', 'Building A', 2500000.00),
('Human Resources', 'Building B', 800000.00),
('Finance', 'Building C', 1200000.00),
('Marketing', 'Building D', 950000.00),
('Sales', 'Building E', 1800000.00),
('Operations', 'Building F', 1100000.00);

-- ============================================================
-- EMPLOYEES TABLE
-- 50+ employees with realistic attributes
-- CRITICAL REQUIREMENTS:
--   - Some employees have manager_id = NULL (top-level managers)
--   - Some have same salary (for RANK vs DENSE_RANK demos)
--   - Some have same hire_date
--   - Mix of active and inactive employees
--   - Salary range: 40000-150000
-- ============================================================
CREATE TABLE employees (
    emp_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department_id INT REFERENCES departments(dept_id),
    salary NUMERIC(10, 2),
    hire_date DATE,
    manager_id INT REFERENCES employees(emp_id),
    is_active BOOLEAN DEFAULT TRUE
);

-- Engineering Department (dept_id = 1)
INSERT INTO employees (first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active) VALUES
('Alice', 'Chen', 'alice.chen@company.com', 1, 145000.00, '2019-03-15', NULL, TRUE),      -- Engineering Director (no manager)
('Bob', 'Martinez', 'bob.martinez@company.com', 1, 125000.00, '2020-06-01', 1, TRUE),      -- Engineering Manager
('Carol', 'Johnson', 'carol.johnson@company.com', 1, 95000.00, '2021-09-10', 2, TRUE),     -- Senior Engineer
('David', 'Kim', 'david.kim@company.com', 1, 88000.00, '2022-01-15', 2, TRUE),             -- Engineer
('Eva', 'Patel', 'eva.patel@company.com', 1, 88000.00, '2022-01-15', 2, TRUE),             -- Engineer (same salary & hire_date as David - for RANK demos)
('Frank', 'Wilson', 'frank.wilson@company.com', 1, 75000.00, '2023-04-20', 2, TRUE),       -- Junior Engineer
('Grace', 'Lee', 'grace.lee@company.com', 1, 72000.00, '2023-07-01', 2, TRUE),             -- Junior Engineer
('Hank', 'Brown', 'hank.brown@company.com', 1, 68000.00, '2024-02-15', 2, FALSE);          -- Former Engineer (inactive)

-- HR Department (dept_id = 2)
INSERT INTO employees (first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active) VALUES
('Iris', 'Taylor', 'iris.taylor@company.com', 2, 115000.00, '2018-11-01', NULL, TRUE),     -- HR Director (no manager)
('Jack', 'Anderson', 'jack.anderson@company.com', 2, 85000.00, '2021-03-15', 9, TRUE),     -- HR Manager
('Karen', 'Thomas', 'karen.thomas@company.com', 2, 72000.00, '2022-08-20', 10, TRUE),      -- HR Specialist
('Leo', 'Jackson', 'leo.jackson@company.com', 2, 65000.00, '2023-06-01', 10, TRUE),        -- HR Coordinator
('Maria', 'White', 'maria.white@company.com', 2, 62000.00, '2024-01-10', 10, FALSE);       -- Former HR Coordinator (inactive)

-- Finance Department (dept_id = 3)
INSERT INTO employees (first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active) VALUES
('Nathan', 'Harris', 'nathan.harris@company.com', 3, 135000.00, '2017-05-20', NULL, TRUE), -- Finance Director (no manager)
('Olivia', 'Clark', 'olivia.clark@company.com', 3, 105000.00, '2020-09-15', 13, TRUE),     -- Finance Manager
('Peter', 'Lewis', 'peter.lewis@company.com', 3, 82000.00, '2021-11-01', 14, TRUE),        -- Senior Accountant
('Quinn', 'Walker', 'quinn.walker@company.com', 3, 78000.00, '2022-04-10', 14, TRUE),      -- Accountant
('Rachel', 'Hall', 'rachel.hall@company.com', 3, 78000.00, '2022-04-10', 14, TRUE),        -- Accountant (same salary & hire_date as Quinn - for RANK demos)
('Sam', 'Allen', 'sam.allen@company.com', 3, 70000.00, '2023-08-15', 14, TRUE),            -- Junior Accountant
('Tina', 'Young', 'tina.young@company.com', 3, 58000.00, '2024-03-01', 14, FALSE);         -- Former Junior Accountant (inactive)

-- Marketing Department (dept_id = 4)
INSERT INTO employees (first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active) VALUES
('Uma', 'King', 'uma.king@company.com', 4, 120000.00, '2019-01-10', NULL, TRUE),           -- Marketing Director (no manager)
('Victor', 'Wright', 'victor.wright@company.com', 4, 95000.00, '2020-11-20', 20, TRUE),    -- Marketing Manager
('Wendy', 'Lopez', 'wendy.lopez@company.com', 4, 78000.00, '2022-02-28', 21, TRUE),        -- Marketing Specialist
('Xavier', 'Hill', 'xavier.hill@company.com', 4, 72000.00, '2022-10-15', 21, TRUE),        -- Content Creator
('Yara', 'Scott', 'yara.scott@company.com', 4, 68000.00, '2023-05-01', 21, TRUE),          -- Social Media Coordinator
('Zane', 'Green', 'zane.green@company.com', 4, 65000.00, '2023-09-20', 21, FALSE);         -- Former Content Creator (inactive)

-- Sales Department (dept_id = 5)
INSERT INTO employees (first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active) VALUES
('Amy', 'Adams', 'amy.adams@company.com', 5, 130000.00, '2018-07-01', NULL, TRUE),         -- Sales Director (no manager)
('Brian', 'Baker', 'brian.baker@company.com', 5, 110000.00, '2020-02-15', 27, TRUE),       -- Sales Manager
('Cindy', 'Nelson', 'cindy.nelson@company.com', 5, 88000.00, '2021-06-01', 28, TRUE),      -- Senior Sales Rep
('Derek', 'Carter', 'derek.carter@company.com', 5, 82000.00, '2021-06-01', 28, TRUE),      -- Senior Sales Rep (same hire_date as Cindy - for demos)
('Emma', 'Mitchell', 'emma.mitchell@company.com', 5, 75000.00, '2022-09-10', 28, TRUE),    -- Sales Rep
('Felix', 'Perez', 'felix.perez@company.com', 5, 70000.00, '2023-01-15', 28, TRUE),        -- Sales Rep
('Gina', 'Roberts', 'gina.roberts@company.com', 5, 65000.00, '2023-11-01', 28, TRUE),      -- Junior Sales Rep
('Henry', 'Turner', 'henry.turner@company.com', 5, 55000.00, '2024-04-01', 28, TRUE),      -- Sales Trainee
('Ivy', 'Phillips', 'ivy.phillips@company.com', 5, 48000.00, '2024-06-15', 28, FALSE);     -- Former Sales Trainee (inactive)

-- Operations Department (dept_id = 6)
INSERT INTO employees (first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active) VALUES
('James', 'Campbell', 'james.campbell@company.com', 6, 125000.00, '2019-08-15', NULL, TRUE), -- Operations Director (no manager)
('Kelly', 'Parker', 'kelly.parker@company.com', 6, 98000.00, '2021-01-10', 36, TRUE),       -- Operations Manager
('Liam', 'Evans', 'liam.evans@company.com', 6, 78000.00, '2022-05-20', 37, TRUE),           -- Operations Analyst
('Mia', 'Edwards', 'mia.edwards@company.com', 6, 72000.00, '2023-02-01', 37, TRUE),         -- Operations Coordinator
('Noah', 'Collins', 'noah.collins@company.com', 6, 68000.00, '2023-10-15', 37, TRUE),       -- Logistics Coordinator
('Oscar', 'Stewart', 'oscar.stewart@company.com', 6, 52000.00, '2024-05-01', 37, TRUE);     -- Operations Assistant

-- An employee with NULL department_id (for LEFT JOIN / orphan exercises)
INSERT INTO employees (first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active) VALUES
('Paula', 'Morris', 'paula.morris@company.com', NULL, 60000.00, '2024-07-01', NULL, TRUE);  -- Unassigned employee

-- ============================================================
-- PRODUCTS TABLE
-- 15+ products in 4 categories: Software, Hardware, Services, Training
-- One product will have NO sales (for LEFT JOIN exercises)
-- ============================================================
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    unit_price NUMERIC(10, 2)
);

INSERT INTO products (product_name, category, unit_price) VALUES
-- Software
('DataFlow Pro', 'Software', 499.99),
('CloudSync Enterprise', 'Software', 899.99),
('AnalyticsSuite', 'Software', 1299.99),
('SecureVault', 'Software', 399.99),
('AutoReport Generator', 'Software', 249.99),
-- Hardware
('Server Rack X200', 'Hardware', 5499.99),
('Network Switch Pro', 'Hardware', 1299.99),
('Storage Array 10TB', 'Hardware', 2899.99),
('Load Balancer LB-500', 'Hardware', 3499.99),
-- Services
('Implementation Package', 'Services', 15000.00),
('Premium Support Annual', 'Services', 8500.00),
('Custom Integration', 'Services', 12000.00),
('Data Migration Service', 'Services', 9500.00),
-- Training
('SQL Fundamentals Workshop', 'Training', 1500.00),
('Advanced Analytics Certification', 'Training', 3500.00),
('Data Engineering Bootcamp', 'Training', 5000.00),
-- Product with NO sales (for LEFT JOIN exercises)
('Legacy System Module', 'Software', 199.99);

-- ============================================================
-- SALES TABLE
-- 200+ records spanning 12 months
-- CRITICAL REQUIREMENTS:
--   - Some sales have region = NULL (for NULL handling demos)
--   - Regions: North, South, East, West
--   - Seasonal patterns (more sales in Q4)
-- ============================================================
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(emp_id),
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    sale_date DATE NOT NULL,
    region VARCHAR(20)
);

-- Q1 Sales (January - March) - Lower volume (~40 sales)
INSERT INTO sales (employee_id, product_id, quantity, sale_date, region) VALUES
(29, 1, 2, '2025-01-05', 'North'),
(29, 3, 1, '2025-01-08', 'South'),
(30, 6, 1, '2025-01-12', 'East'),
(30, 10, 1, '2025-01-15', 'West'),
(31, 2, 3, '2025-01-18', 'North'),
(32, 14, 5, '2025-01-22', 'South'),
(33, 7, 2, '2025-01-25', NULL),
(34, 4, 1, '2025-01-28', 'East'),
(29, 11, 1, '2025-02-02', 'West'),
(30, 1, 4, '2025-02-05', 'North'),
(31, 8, 1, '2025-02-08', 'South'),
(32, 15, 2, '2025-02-12', 'East'),
(33, 3, 1, '2025-02-15', 'West'),
(34, 12, 1, '2025-02-18', 'North'),
(29, 5, 3, '2025-02-22', 'South'),
(30, 9, 1, '2025-02-25', NULL),
(31, 1, 2, '2025-03-01', 'East'),
(32, 6, 1, '2025-03-05', 'West'),
(33, 16, 1, '2025-03-08', 'North'),
(34, 2, 2, '2025-03-12', 'South'),
(29, 13, 1, '2025-03-15', 'East'),
(30, 4, 3, '2025-03-18', 'West'),
(31, 7, 1, '2025-03-22', 'North'),
(32, 10, 1, '2025-03-25', 'South'),
(33, 1, 2, '2025-03-28', NULL);

-- Q2 Sales (April - June) - Moderate volume (~50 sales)
INSERT INTO sales (employee_id, product_id, quantity, sale_date, region) VALUES
(34, 3, 1, '2025-04-02', 'East'),
(29, 8, 2, '2025-04-05', 'West'),
(30, 14, 3, '2025-04-08', 'North'),
(31, 11, 1, '2025-04-12', 'South'),
(32, 1, 5, '2025-04-15', 'East'),
(33, 5, 2, '2025-04-18', 'West'),
(34, 9, 1, '2025-04-22', 'North'),
(29, 16, 1, '2025-04-25', 'South'),
(30, 2, 2, '2025-04-28', NULL),
(31, 6, 1, '2025-05-02', 'East'),
(32, 12, 1, '2025-05-05', 'West'),
(33, 3, 2, '2025-05-08', 'North'),
(34, 7, 3, '2025-05-12', 'South'),
(29, 15, 1, '2025-05-15', 'East'),
(30, 4, 1, '2025-05-18', 'West'),
(31, 10, 2, '2025-05-22', 'North'),
(32, 1, 3, '2025-05-25', 'South'),
(33, 13, 1, '2025-05-28', NULL),
(34, 8, 1, '2025-06-01', 'East'),
(29, 2, 2, '2025-06-05', 'West'),
(30, 11, 1, '2025-06-08', 'North'),
(31, 5, 4, '2025-06-12', 'South'),
(32, 9, 1, '2025-06-15', 'East'),
(33, 16, 2, '2025-06-18', 'West'),
(34, 3, 1, '2025-06-22', 'North'),
(29, 6, 1, '2025-06-25', 'South'),
(30, 14, 2, '2025-06-28', NULL);

-- Q3 Sales (July - September) - Growing volume (~55 sales)
INSERT INTO sales (employee_id, product_id, quantity, sale_date, region) VALUES
(31, 1, 3, '2025-07-02', 'East'),
(32, 7, 2, '2025-07-05', 'West'),
(33, 12, 1, '2025-07-08', 'North'),
(34, 4, 2, '2025-07-12', 'South'),
(29, 15, 1, '2025-07-15', 'East'),
(30, 10, 2, '2025-07-18', 'West'),
(31, 2, 1, '2025-07-22', 'North'),
(32, 8, 1, '2025-07-25', 'South'),
(33, 5, 3, '2025-07-28', NULL),
(34, 13, 1, '2025-08-01', 'East'),
(29, 3, 2, '2025-08-05', 'West'),
(30, 9, 1, '2025-08-08', 'North'),
(31, 16, 1, '2025-08-12', 'South'),
(32, 1, 4, '2025-08-15', 'East'),
(33, 6, 1, '2025-08-18', 'West'),
(34, 11, 2, '2025-08-22', 'North'),
(29, 14, 3, '2025-08-25', 'South'),
(30, 7, 1, '2025-08-28', NULL),
(31, 4, 2, '2025-09-01', 'East'),
(32, 2, 1, '2025-09-05', 'West'),
(33, 12, 1, '2025-09-08', 'North'),
(34, 15, 2, '2025-09-12', 'South'),
(29, 8, 1, '2025-09-15', 'East'),
(30, 5, 2, '2025-09-18', 'West'),
(31, 10, 1, '2025-09-22', 'North'),
(32, 3, 3, '2025-09-25', 'South'),
(33, 1, 2, '2025-09-28', NULL);

-- Q4 Sales (October - December) - Higher volume (~65+ sales) - End of year push
INSERT INTO sales (employee_id, product_id, quantity, sale_date, region) VALUES
(34, 6, 2, '2025-10-02', 'East'),
(29, 9, 1, '2025-10-05', 'West'),
(30, 13, 1, '2025-10-08', 'North'),
(31, 2, 3, '2025-10-12', 'South'),
(32, 7, 2, '2025-10-15', 'East'),
(33, 16, 2, '2025-10-18', 'West'),
(34, 4, 1, '2025-10-22', 'North'),
(29, 11, 2, '2025-10-25', 'South'),
(30, 1, 5, '2025-10-28', NULL),
(31, 8, 1, '2025-11-01', 'East'),
(32, 14, 4, '2025-11-05', 'West'),
(33, 3, 2, '2025-11-08', 'North'),
(34, 10, 2, '2025-11-12', 'South'),
(29, 5, 3, '2025-11-15', 'East'),
(30, 12, 1, '2025-11-18', 'West'),
(31, 6, 2, '2025-11-22', 'North'),
(32, 15, 1, '2025-11-25', 'South'),
(33, 2, 2, '2025-11-28', NULL),
(34, 9, 1, '2025-12-01', 'East'),
(29, 4, 2, '2025-12-05', 'West'),
(30, 11, 1, '2025-12-08', 'North'),
(31, 16, 3, '2025-12-12', 'South'),
(32, 1, 6, '2025-12-15', 'East'),
(33, 7, 1, '2025-12-18', 'West'),
(34, 13, 2, '2025-12-20', 'North'),
(29, 3, 2, '2025-12-22', 'South'),
(30, 8, 1, '2025-12-24', NULL),
(31, 14, 5, '2025-12-26', 'East'),
(32, 10, 2, '2025-12-28', 'West'),
(33, 5, 4, '2025-12-30', 'North');

-- Additional sales from employees in other departments (Engineering, HR, Finance, etc.)
-- This adds realism and variety to the dataset
INSERT INTO sales (employee_id, product_id, quantity, sale_date, region) VALUES
(3, 1, 1, '2025-02-10', 'North'),
(4, 2, 1, '2025-03-15', 'East'),
(5, 3, 1, '2025-04-20', 'South'),
(6, 5, 2, '2025-05-25', 'West'),
(7, 4, 1, '2025-06-30', NULL),
(11, 14, 3, '2025-07-05', 'North'),
(12, 15, 1, '2025-08-10', 'South'),
(13, 16, 1, '2025-09-15', 'East'),
(14, 1, 2, '2025-10-20', 'West'),
(15, 3, 1, '2025-11-25', 'North'),
(22, 2, 1, '2025-03-05', 'South'),
(23, 10, 1, '2025-05-10', 'East'),
(24, 12, 1, '2025-07-15', 'West'),
(25, 13, 1, '2025-09-20', 'North'),
(26, 11, 1, '2025-11-30', 'South'),
(38, 14, 2, '2025-04-12', 'East'),
(39, 15, 1, '2025-06-18', 'West'),
(40, 16, 1, '2025-08-22', 'North'),
(41, 5, 1, '2025-10-28', 'South');

-- ============================================================
-- VERIFICATION QUERIES (run to confirm dataset was created)
-- ============================================================

-- Check table counts
SELECT 'departments' AS table_name, COUNT(*) AS row_count FROM company.departments
UNION ALL
SELECT 'employees', COUNT(*) FROM company.employees
UNION ALL
SELECT 'products', COUNT(*) FROM company.products
UNION ALL
SELECT 'sales', COUNT(*) FROM company.sales;

-- Check for key requirements:
-- 1. Employees with NULL manager_id (top-level managers)
SELECT COUNT(*) AS top_level_managers FROM company.employees WHERE manager_id IS NULL;

-- 2. Employees with same salary (for RANK demos)
SELECT salary, COUNT(*) AS count FROM company.employees GROUP BY salary HAVING COUNT(*) > 1;

-- 3. Sales with NULL region
SELECT COUNT(*) AS sales_with_null_region FROM company.sales WHERE region IS NULL;

-- 4. Department with no employees (should be 0 - all departments have employees)
-- Actually, let's verify all departments have employees
SELECT d.dept_id, d.dept_name, COUNT(e.emp_id) AS employee_count
FROM company.departments d
LEFT JOIN company.employees e ON d.dept_id = e.department_id
GROUP BY d.dept_id, d.dept_name;

-- 5. Product with no sales (product_id = 17, Legacy System Module)
SELECT p.product_id, p.product_name, COUNT(s.sale_id) AS sale_count
FROM company.products p
LEFT JOIN company.sales s ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name
HAVING COUNT(s.sale_id) = 0;
