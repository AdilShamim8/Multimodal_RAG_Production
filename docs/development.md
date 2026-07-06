# Development guide

## Setup

```bash
make dev-install   # installs dev + gpu + docs extras
make lint
make type-check
make test
```

## Layout

```
src/multimodal_rag/    <- package source
tests/                 <- pytest unit + integration tests
scripts/               <- one-off scripts (sample dataset, prometheus.yml)
notebooks/             <- original notebook preserved for reference
docs/                  <- this folder
```

## Running tests with coverage

```bash
make test-cov
# open htmlcov/index.html in a browser
```

Target: ≥ 80% coverage on `src/multimodal_rag/`.

## Adding a new provider

1. Implement the relevant Protocol (`Embedder`, `Reranker`, or `Generator`).
2. Add it to the factory `build_*` function.
3. Add an env-var Literal type in `Settings`.
4. Add tests under `tests/test_<family>.py`.
5. Update `.env.example` and `docs/architecture.md`.

## Adding a new vector store

1. Implement the `VectorStore` protocol in `stores/<name>_store.py`.
2. Wire it into `stores/factory.py`.
3. Add tests in `tests/test_stores.py`.
4. Update `docs/architecture.md`.

## Re-generating the sample dataset

```bash
python scripts/build_sample_dataset.py
cp data/sample_recipes.json src/multimodal_rag/data/sample_recipes.json
```

## Release checklist

- [ ] Bump `__version__` in `_version.py` and `pyproject.toml`
- [ ] Update `CHANGELOG.md`
- [ ] `make lint && make type-check && make test`
- [ ] Tag and push: `git tag v1.x.y && git push --tags`
- [ ] GitHub Actions will run CI and build the Docker image
