"""Shared test fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Force mock providers + tiny in-memory vector store BEFORE any settings load.
os.environ.setdefault("EMBEDDING_PROVIDER", "mock")
os.environ.setdefault("RERANKER_PROVIDER", "mock")
os.environ.setdefault("GENERATOR_PROVIDER", "mock")
os.environ.setdefault("VECTOR_STORE", "chroma")
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/mrag-test-chroma")
os.environ.setdefault("DATASET_SOURCE", "sample")
os.environ.setdefault("APP_LOG_LEVEL", "WARNING")
os.environ.setdefault("CACHE_ENABLED", "false")

# Clear cached settings so the env vars above take effect.
from multimodal_rag.config import get_settings  # noqa: E402

get_settings.cache_clear()


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def recipes():
    from multimodal_rag.data import build_dataset_loader
    return build_dataset_loader().load(source="sample", limit=20)


@pytest.fixture()
def pipeline(recipes):
    """A RAG pipeline with mock providers + a freshly-wiped Chroma store."""
    from multimodal_rag.pipeline import build_rag_pipeline

    p = build_rag_pipeline()
    p.store.delete_all()
    p.ingest(recipes)
    yield p
    p.store.delete_all()


@pytest.fixture()
def client(pipeline):
    """A FastAPI TestClient with the pipeline dependency overridden."""
    from fastapi.testclient import TestClient

    from multimodal_rag.api.deps import get_pipeline
    from multimodal_rag.app import create_app

    app = create_app()
    app.dependency_overrides[get_pipeline] = lambda: pipeline
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# Ensure test data dirs exist
Path("/tmp/mrag-test-chroma").mkdir(parents=True, exist_ok=True)
