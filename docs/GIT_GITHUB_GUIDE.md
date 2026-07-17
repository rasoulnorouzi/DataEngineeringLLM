# Git & GitHub Guide — the workflow you'll use in every project

> Read this before starting any `project-*/` folder. You'll use this exact workflow in every module
> and in every real engineering job.

---

## Why Git exists (the WHY, as always)

Imagine writing your thesis and saving files like `thesis_final.docx`, `thesis_final_v2.docx`,
`thesis_FINAL_really.docx`. Now imagine three people editing them at once, by email. Chaos.

Git solves this: it's a **time machine plus collaboration protocol** for folders of files.
Every "save point" (commit) records *what* changed, *who* changed it, and *why* (the message).
You can go back to any point, work on parallel versions (branches), and merge them safely.

GitHub is a **hosting service** for Git repositories, plus collaboration features (pull requests,
issues, CI with GitHub Actions). Git works fine without GitHub; GitHub is where your portfolio lives.

---

## The 10 commands you'll actually use

```bash
git status                  # what changed? (run this constantly)
git add <file>              # stage a change ("put it in the box")
git add -A                  # stage everything
git commit -m "message"     # seal the box with a label
git log --oneline           # history
git diff                    # what changed since last commit (unstaged)
git switch -c my-feature    # create + switch to a branch
git switch main             # go back to main
git merge my-feature        # bring branch changes into current branch
git push / git pull         # sync with GitHub (up / down)
```

**Mental model:** working folder → (`git add`) → staging area → (`git commit`) → history.
The staging area exists so you can commit *part* of your changes as one logical unit.

---

## Commit messages that don't suck

Bad: `fix`, `changes`, `asdf`
Good: `Add row validation to ingest step`, `Fix off-by-one in weekly aggregation window`

Rule of thumb: finish the sentence *"If applied, this commit will …"*. Keep the first line ≤ 50–70
characters. Explain *why* in the body if it's not obvious.

---

## The professional loop (used in all projects here)

1. `git switch -c feature/ingest-knmi` — never work directly on `main` in a team setting
2. Small commits as you go, each one a working state
3. `git push -u origin feature/ingest-knmi`
4. Open a **Pull Request** on GitHub — even solo: it's where CI runs and where you review your own diff
5. CI (GitHub Actions) runs lint + tests automatically — green check required
6. Merge to `main`. `main` stays always-working.

This solo-PR habit is exactly what interviewers want to see in your portfolio repos: a `main` branch
with green CI and a history of meaningful PRs.

---

## Publishing a course project as a portfolio repo

Each `project-*/` folder in this course is self-contained on purpose. To publish one:

```bash
# 1. Create an empty repo on GitHub (no README), e.g. nl-open-data-pipeline
# 2. Copy the project folder somewhere outside this course repo, then inside it:
git init
git add -A
git commit -m "Initial commit: NL open data pipeline"
git branch -M main
git remote add origin https://github.com/<you>/nl-open-data-pipeline.git
git push -u origin main
```

The `.github/workflows/` folder inside the project starts working immediately — your CI badge goes
green on the first push. Add the badge to the README:

```markdown
![CI](https://github.com/<you>/nl-open-data-pipeline/actions/workflows/ci.yml/badge.svg)
```

---

## .gitignore essentials

Never commit: `.venv/`, `__pycache__/`, `.env` (secrets!), database volumes, large generated
outputs. Every project here ships a `.gitignore` — read it once to see what's excluded and why.

---

## When things go wrong (the honest cheat sheet)

```bash
git restore <file>            # discard uncommitted changes to a file (careful: gone for good)
git restore --staged <file>   # un-stage (keeps your edits)
git commit --amend            # fix the last commit message (only if not pushed yet)
git log --oneline             # find a commit hash...
git revert <hash>             # ...and safely undo it with a new commit (history preserved)
```

Golden rule: if it's committed, it's almost never lost. Commit early, commit often.
