.PHONY: help install dev-install lint type-check test test-cov clean serve ingest docker-build docker-up docker-down docs

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install runtime deps (mock providers only)
	pip install -e .

dev-install:  ## Install with dev + gpu extras
	pip install -e ".[dev,gpu,docs]"

lint:  ## Run ruff
	ruff check src tests

lint-fix:  ## Auto-fix lint issues
	ruff check --fix src tests

type-check:  ## Run mypy
	mypy src

test:  ## Run pytest
	pytest

test-cov:  ## Run pytest with coverage report
	pytest --cov-report=html

serve:  ## Start the FastAPI server (uvicorn)
	uvicorn multimodal_rag.app:app --reload --host 0.0.0.0 --port 8000

ingest:  ## Ingest sample dataset into vector store
	multimodal-rag ingest --source sample

ingest-full:  ## Ingest full 10k HuggingFace dataset
	multimodal-rag ingest --source hf

download-models:  ## Pre-download HF model weights (only needed for local_hf providers)
	multimodal-rag download-models

docker-build:  ## Build the Docker image
	docker build -t multimodal-rag:latest .

docker-up:  ## Start the full Docker Compose stack
	docker compose up -d

docker-down:  ## Stop the Docker Compose stack
	docker compose down

docker-logs:  ## Tail Docker Compose logs
	docker compose logs -f

docs:  ## Generate the DOCX documentation
	python scripts/generate_docs.py

clean:  ## Remove caches + build artifacts
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
