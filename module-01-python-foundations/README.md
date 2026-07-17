# Module 1 — Professional Python & Engineering Habits

**Duration:** 2 weeks (~10 hrs/week) · **Status:** lessons ready (from course v1), project layer pending

## Learning Goals

- Write typed, structured Python: type hints, dataclasses, **Pydantic** for validation
- Work with data: NumPy, pandas, pathlib, logging
- **New (project layer, to be authored):** project layout with `pyproject.toml`, virtual
  environments, Git/GitHub workflow, **pytest** fundamentals, **ruff** linting, and your first
  **GitHub Actions CI** pipeline (lint + test on every push)

## Portfolio Project: `datacli`

A typed, tested, installable command-line tool (built with Typer) that:
- ingests messy CSVs (the module's sample datasets)
- validates rows with Pydantic (bad rows quarantined with reasons)
- emits cleaned Parquet + a summary report

Deliverable: a public repo with a **green CI badge** — your first portfolio piece.

> *CV bullet:* "Built and published a tested, typed Python CLI for data validation and
> transformation with automated linting and testing via GitHub Actions CI."

## Contents

- [lessons/](lessons/) — the original Week-1 notebook + data (already complete; work through
  `01_python_for_data.ipynb`, reference outputs in `01_python_for_data_executed.ipynb`)
- `exercises/` — (to be added in the retrofit session)
- `project-datacli/` — (to be added in the retrofit session)

**Note:** if you already completed course-v1 Week 1, skip the lessons — only the project layer is
new. The pytest + GitHub Actions essentials are also covered by Module 2's bridge lesson, so you
can safely do Module 2 before this module's project.
