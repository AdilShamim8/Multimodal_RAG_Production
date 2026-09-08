# Engineering Journal

> Append-only log of major development steps. Updated as the project evolves.

## Template

```
## YYYY-MM-DD — Phase N: [phase name]

### Goal
What we set out to do.

### What changed
- file 1
- file 2

### Why
The reasoning behind the changes.

### Implementation
Key technical decisions and approaches.

### Tests
What was tested and how.

### Results
Measured outcomes.

### Problems
Issues encountered.

### Fix
How we fixed them.

### Trade-offs
What we gave up.

### Lessons learned
What to do differently next time.

### Next step
What's next.
```

---

## YYYY-MM-DD — Phase 0: Repo Bootstrap

### Goal
Set up the repository skeleton with directory structure, tooling, and CI.

### What changed
- Created `apps/`, `src/`, `tests/`, `evals/`, `prompts/`, `configs/`, `docs/`, `infra/`, `docker/`, `.github/` directories.
- Added `pyproject.toml`, `Makefile`, `docker-compose.yml`, `.env.example`, `.gitignore`.
- Added pre-commit hooks (ruff, black, mypy, detect-secrets).

### Why
Every later phase needs a home. Setting up tooling first prevents drift.

### Implementation
Standard Python project layout with `src/` for library code and `apps/` for runnable applications.

### Tests
`make lint && make test` passes on an empty implementation.

### Results
Clean repo, ready for Phase 1.

### Problems
None.

### Fix
n/a.

### Trade-offs
We chose a monorepo (api + web + workers together) over separate repos. Easier for one engineer to manage; harder at org scale.

### Lessons learned
n/a.

### Next step
Phase 1: discovery + architecture.

---

(Continue adding entries as you build. Honest documentation of failures is engineering evidence.)
