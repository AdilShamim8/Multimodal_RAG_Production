# =============================================================================
# Makefile — Agentic RAG Platform
# All common commands. Run `make help` to see the list.
# =============================================================================

.PHONY: help up down restart logs ps migrate migrate-down seed db-reset \
        ingest-local ingest-web ingest-github \
        test test-unit test-integration test-security test-e2e test-regression \
        eval eval-smoke eval-compare eval-baseline-1 eval-baseline-2 eval-baseline-3 \
        eval-baseline-4 eval-baseline-5 eval-baseline-6 \
        lint format type-check \
        bench clean install-dev install-web \
        docker-build docker-push \
        release validate-release

PYTHON := python
PIP := pip
COMPOSE := docker compose
ALEMBIC := alembic

# Default target
.DEFAULT_GOAL := help

help: ## Show this help
	@echo "Agentic RAG Platform — available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# -----------------------------------------------------------------------------
# Docker stack
# -----------------------------------------------------------------------------

up: ## Start all services (postgres, api, web, worker, langfuse)
	$(COMPOSE) up -d
	@echo "Stack is up. API: http://localhost:8000  Web: http://localhost:3000  Langfuse: http://localhost:3001"

down: ## Stop all services
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

logs: ## Tail logs from all services
	$(COMPOSE) logs -f --tail=100

ps: ## Show running services
	$(COMPOSE) ps

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

migrate: ## Apply database migrations
	$(PYTHON) -m alembic upgrade head

migrate-down: ## Roll back the last migration
	$(PYTHON) -m alembic downgrade -1

migrate-new: ## Create a new migration (usage: make migrate-new NAME=add_foo_table)
	$(PYTHON) -m alembic revision --autogenerate -m "$(NAME)"

db-reset: ## DANGEROUS: drop + recreate + migrate + seed
	$(COMPOSE) down -v
	$(COMPOSE) up -d postgres
	@sleep 5
	$(PYTHON) -m alembic upgrade head
	$(PYTHON) -m scripts.seed

seed: ## Load demo users, roles, departments
	$(PYTHON) -m scripts.seed

# -----------------------------------------------------------------------------
# Ingestion
# -----------------------------------------------------------------------------

ingest-local: ## Ingest documents from data/sources/local/
	$(PYTHON) -m scripts.ingest --source local --path data/sources/local/ --strategy structure-aware

ingest-web: ## Ingest documents from a web URL (usage: make ingest-web URL=https://example.com/docs)
	$(PYTHON) -m scripts.ingest --source web --url $(URL) --strategy structure-aware

ingest-github: ## Ingest documents from a GitHub repo (usage: make ingest-github REPO=owner/repo)
	$(PYTHON) -m scripts.ingest --source github --repo $(REPO) --strategy structure-aware

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

test: test-unit test-integration ## Run all tests

test-unit: ## Run unit tests only
	$(PYTHON) -m pytest tests/unit -v --cov=src --cov-report=term-missing

test-integration: ## Run integration tests (requires running stack)
	$(PYTHON) -m pytest tests/integration -v

test-security: ## Run security tests (RBAC, prompt injection)
	$(PYTHON) -m pytest tests/security -v

test-e2e: ## Run end-to-end tests
	$(PYTHON) -m pytest tests/e2e -v

test-regression: ## Run regression tests (golden dataset, RBAC, agent termination)
	$(PYTHON) -m pytest tests/regression -v

# -----------------------------------------------------------------------------
# Evaluation
# -----------------------------------------------------------------------------

eval: ## Run full evaluation on the golden dataset
	$(PYTHON) -m evals.run --dataset evals/datasets/golden.jsonl --all-baselines

eval-smoke: ## Run 10-item smoke eval (used in CI)
	$(PYTHON) -m evals.run --dataset evals/datasets/golden_smoke.jsonl --baselines baseline_5_hybrid_reranked

eval-compare: ## Generate evals/reports/comparison.md across all baselines
	$(PYTHON) -m evals.compare --reports-dir evals/reports/

eval-baseline-1: ## Run baseline 1 (naive RAG)
	$(PYTHON) -m evals.run --baseline evals/baselines/baseline_1_naive.json

eval-baseline-2: ## Run baseline 2 (dense only)
	$(PYTHON) -m evals.run --baseline evals/baselines/baseline_2_dense.json

eval-baseline-3: ## Run baseline 3 (lexical only)
	$(PYTHON) -m evals.run --baseline evals/baselines/baseline_3_lexical.json

eval-baseline-4: ## Run baseline 4 (hybrid)
	$(PYTHON) -m evals.run --baseline evals/baselines/baseline_4_hybrid.json

eval-baseline-5: ## Run baseline 5 (hybrid + rerank)
	$(PYTHON) -m evals.run --baseline evals/baselines/baseline_5_hybrid_reranked.json

eval-baseline-6: ## Run baseline 6 (agentic)
	$(PYTHON) -m evals.run --baseline evals/baselines/baseline_6_agentic.json

# -----------------------------------------------------------------------------
# Code quality
# -----------------------------------------------------------------------------

lint: ## Run ruff + black --check + mypy
	ruff check src tests apps scripts evals
	black --check src tests apps scripts evals
	mypy src

format: ## Auto-format with ruff + black
	ruff check --fix src tests apps scripts evals
	black src tests apps scripts evals

type-check: ## Run mypy only
	mypy src

# -----------------------------------------------------------------------------
# Performance
# -----------------------------------------------------------------------------

bench: ## Run performance benchmarks
	$(PYTHON) -m scripts.bench --output docs/operations/performance.md

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

install-dev: ## Install Python dev dependencies
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && $(PIP) install -e ".[dev]"
	. .venv/bin/activate && pre-commit install

install-web: ## Install frontend dependencies
	cd apps/web && npm install

# -----------------------------------------------------------------------------
# Docker build
# -----------------------------------------------------------------------------

docker-build: ## Build all Docker images
	$(COMPOSE) build

docker-push: ## Push images to registry (requires REGISTRY env var)
	$(COMPOSE) build
	$(COMPOSE) push

# -----------------------------------------------------------------------------
# Release
# -----------------------------------------------------------------------------

validate-release: ## Validate the release (checks required files, no secrets)
	./scripts/validate_release.sh

release: validate-release ## Build the release ZIP
	./scripts/build_release.sh

clean: ## Remove build artifacts and caches
	rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	cd apps/web && rm -rf .next node_modules || true
	@echo "Cleaned."
