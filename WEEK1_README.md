# Week 1 — Python for Data Engineering

## 📚 Overview

This week focuses on writing **clean, professional Python code** for data engineering. You'll master the foundational tools through detailed explanations and hands-on practice.

---

## 🎯 What You'll Learn

### 1. **Environment Setup** (pyenv & venv)
**What it is**: Tools to manage Python versions and isolate project dependencies

**Why it matters**: Without environments, projects conflict with each other. Think of it like having separate kitchens for Italian and Japanese cooking — you don't want to mix soy sauce with pasta!

**You'll learn**:
- Why environments exist and when to use them
- How to create and activate virtual environments
- How to install packages safely
- Best practices for project isolation

---

### 2. **Type Hints**
**What they are**: Annotations that tell humans and tools what type of data your code expects

**Why they matter**: Without type hints, your code is like a recipe without measurements. Type hints make your code self-documenting and catch errors before you run it.

**You'll learn**:
- The problem with untyped code (with examples)
- Basic types: `int`, `float`, `str`, `bool`
- Complex types: `List`, `Dict`, `Optional`, `Union`
- How to write functions with full type annotations
- Why modern Python codebases require type hints

---

### 3. **Dataclasses**
**What they are**: A Python feature that automatically generates boilerplate code for data storage classes

**Why they matter**: Without dataclasses, you write 10+ lines of repetitive code just to store 3 pieces of data. With dataclasses, it's 4 lines!

**You'll learn**:
- The boilerplate problem (side-by-side comparison)
- How `@dataclass` eliminates repetitive code
- Default values and `field(default_factory=...)`
- Adding methods to dataclasses
- When to use dataclasses vs regular classes

---

### 4. **NumPy** (Numerical Python)
**What it is**: A library for fast mathematical operations on arrays

**Why it matters**: NumPy is **50-100x faster** than Python loops for math. It's the foundation of pandas, scikit-learn, TensorFlow, and PyTorch.

**You'll learn**:
- Why Python lists are slow for math
- What vectorization means (operations without loops)
- Creating arrays (1D, 2D, 3D)
- Mathematical operations and functions
- Boolean indexing (filtering with conditions)
- Aggregation functions (sum, mean, std, etc.)
- Broadcasting (automatic array alignment)

---

### 5. **pandas** (Data Manipulation)
**What it is**: A library for working with tabular data (like Excel in Python)

**Why it matters**: Data engineers spend 80% of their time cleaning and transforming data. Pandas makes this fast and easy.

**You'll learn**:
- Creating and loading DataFrames
- Exploring data (head, describe, info)
- Selecting columns and rows
- Filtering with conditions
- GroupBy operations (like Excel pivot tables)
- Merging/joining tables (like SQL JOIN)
- Handling missing data
- Working with real datasets (barbie.csv)

---

### 6. **pathlib** (File System Operations)
**What it is**: Python's modern, object-oriented way to work with file paths

**Why it matters**: The old `os.path` approach is clunky and error-prone. pathlib is cleaner, more readable, and cross-platform.

**You'll learn**:
- The problem with `os.path` (with examples)
- Creating Path objects
- Joining paths with `/` operator
- File and directory operations
- Finding files with glob patterns
- Reading and writing files

---

### 7. **Logging** (Professional Debugging)
**What it is**: A way to record messages about what your program is doing

**Why it matters**: Using `print()` in production code is amateurish. Logging is professional, configurable, and industry-standard.

**You'll learn**:
- Why `print()` is bad practice (5 reasons)
- Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Setting up loggers
- Logging to console and files
- Using logging in data processing functions
- Best practices for production code

---

### 8. **Comprehensive Project**
**What it is**: A production-ready data pipeline combining all concepts

**Why it matters**: This is exactly what data engineers do in real jobs!

**You'll build**:
- A configurable pipeline with dataclasses
- Type hints throughout
- File discovery with pathlib
- Data loading and validation with pandas
- Progress tracking with logging
- Error handling and reporting

---

## 📂 Files Included

- **`week1_python_for_data.ipynb`** — Blank notebook (no outputs)
- **`week1_python_for_data_executed.ipynb`** — Pre-executed with all outputs
- **`barbie.csv`** — Sample dataset for exercises
- **`sample_sales.csv`** — Generated during exercises
- **`WEEK1_README.md`** — This file
- **`build_week1_notebook.py`** — Script that generates the notebook

---

## 🚀 How to Use

### Option 1: Learn by Doing (Recommended)
```bash
# Navigate to project directory
cd /home/rass/Downloads/projects/LLM_engineer

# Activate virtual environment
source myenv/bin/activate

# Start Jupyter
jupyter notebook

# Open: week1_python_for_data.ipynb
# Read the theory, then run each cell yourself!
```

### Option 2: See All Outputs
```bash
# Open the pre-executed version
jupyter notebook week1_python_for_data_executed.ipynb
```

---

## 📖 How to Study

**This is NOT a reference manual.** This is a **guided learning experience**.

### For Each Section:
1. 📖 **Read the theory first** — understand WHAT and WHY
2. 💻 **Run every code cell** — see it in action
3. 🔍 **Study the output** — understand WHY it looks like that
4. ✏️ **Try the exercises** — practice makes permanent
5. ❓ **Ask "why?" often** — curiosity drives learning

### Learning Philosophy
- **Start simple** → Build to professional
- **Understand why** → Before learning how
- **See it work** → Then write it yourself

---

## ⏱️ Expected Time Commitment

- **Reading + Running examples**: 4-6 hours
- **Completing exercises**: 2-3 hours  
- **Practice and review**: 2-3 hours
- **Total**: ~10 hours over 5-7 days

**Don't rush!** Master each concept before moving to the next.

---

## 💡 Exercises

The notebook includes **6 hands-on exercises** with complete solutions:

1. **Exercise 1**: Normalize scores with type hints
2. **Exercise 2**: Create Product dataclass
3. **Exercise 3**: NumPy array operations
4. **Exercise 4**: Pandas data analysis
5. **Exercise 5**: File management with pathlib
6. **Exercise 6**: Data validation with logging

---

## 🎓 What Makes This Tutorial Different

### ✅ Extensive Theory
Every concept is explained **before** showing code, with:
- Real-world analogies
- "Bad way" vs "Good way" comparisons
- Detailed explanations of WHY things exist
- Step-by-step progression from simple to complex

### ✅ Beginner-Friendly
Written for someone who has **never seen these concepts before**:
- No assumptions about prior knowledge
- Every error message explained
- Every parameter documented
- Every output analyzed

### ✅ Production-Ready
Teaches professional practices from day one:
- Type hints throughout
- Comprehensive docstrings
- Proper error handling
- Industry-standard logging

---

## 📚 Additional Resources

- **pandas**: https://pandas.pydata.org/docs/
- **numpy**: https://numpy.org/doc/
- **pathlib**: https://docs.python.org/3/library/pathlib.html
- **logging**: https://docs.python.org/3/library/logging.html
- **Type hints**: https://docs.python.org/3/library/typing.html
- **Dataclasses**: https://docs.python.org/3/library/dataclasses.html

---

## 🎯 Next Steps

After completing Week 1:
- Practice daily with real datasets
- Refactor old code to use type hints
- Replace print statements with logging
- Start using pathlib instead of os.path
- Prepare for Week 2!

---

**Created**: 2026-04-11  
**Python Version**: 3.13.5  
**Status**: ✅ Ready to use and fully tested
