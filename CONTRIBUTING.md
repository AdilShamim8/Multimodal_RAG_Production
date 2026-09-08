# Contributing

Thanks for your interest in contributing! This project follows a structured workflow.

## Development setup

See [QUICKSTART.md](QUICKSTART.md) for local setup.

## Workflow

1. **Open an issue** describing what you want to change and why.
2. **Fork + branch** from `main`: `git checkout -b feat/your-feature`.
3. **Write tests first** (TDD-lite): write a failing test, then implement.
4. **Run quality checks**:
   ```bash
   make lint
   make test
   make eval-smoke
   ```
5. **Open a PR** with a clear description. CI must pass.
6. **Address review feedback**.
7. **Squash merge** to `main`.

## Code style

- Python: ruff + black + mypy strict. Run `make format` to auto-fix.
- TypeScript: ESLint + Prettier (configured in `apps/web`).
- Commit messages: `<type>(<scope>): <subject>` (e.g., `feat(retrieval): add HNSW index option`).

## Architecture changes

Any change to a component covered by an ADR requires either:
- Updating the ADR (if extending the decision), or
- A new ADR (if superseding it).

See [`docs/decisions/`](docs/decisions/) for existing ADRs.

## Adding a new tool

1. Create `src/agents/tools/your_tool.py`.
2. Use the `@register_tool` decorator with a JSON schema.
3. Add a test in `tests/unit/test_your_tool.py`.
4. Document in `docs/learning/`.

## Adding a new eval metric

1. Implement in `src/evaluation/`.
2. Add to `evals/run.py` aggregation.
3. Add to the comparison report.
4. If it's a quality gate, add to CI in `.github/workflows/ci.yml`.

## Adding a new source connector

1. Implement the `Fetcher` protocol in `src/ingestion/fetchers/`.
2. Add to `scripts/ingest.py` CLI.
3. Document in `docs/learning/`.

## Reporting security issues

**Do not open a public GitHub issue.** Email `security@your-org.example` (replace with your real address). We respond within 72 hours.

## License

By contributing, you agree that your contributions are licensed under the MIT license.
