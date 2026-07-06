"""Tests for the vector store implementations."""

from __future__ import annotations

import numpy as np
import pytest

from multimodal_rag.schemas import Recipe
from multimodal_rag.stores.base import VectorRecord


def _make_recipe(i: int) -> Recipe:
    return Recipe(
        id=f"r{i}",
        title=f"Recipe {i}",
        text=f"text {i}",
        metadata={"cuisine": "italian" if i % 2 == 0 else "thai"},
    )


def _random_vec(dim: int = 128, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(dim).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-12)


def test_vector_record_from_recipe():
    r = _make_recipe(1)
    v = _random_vec(seed=1)
    rec = VectorRecord.from_recipe(r, v)
    assert rec.id == "r1"
    assert len(rec.vector) == 128
    assert rec.payload["title"] == "Recipe 1"


@pytest.mark.parametrize("store_name", ["chroma", "faiss"])
def test_store_roundtrip(store_name, tmp_path):
    if store_name == "chroma":
        from multimodal_rag.stores.chroma_store import ChromaStore
        store = ChromaStore(persist_dir=str(tmp_path / "chroma"))
    else:
        from multimodal_rag.stores.faiss_store import FAISSStore
        store = FAISSStore(index_path=str(tmp_path / "faiss" / "i.faiss"), dim=128)

    recipes = [_make_recipe(i) for i in range(10)]
    records = [
        VectorRecord.from_recipe(r, _random_vec(seed=i)) for i, r in enumerate(recipes)
    ]
    n = store.upsert(records)
    assert n == 10
    assert store.count() == 10

    # Search with the first recipe's vector → should rank it first
    q = _random_vec(seed=0)
    hits = store.search(q, top_k=3)
    assert len(hits) == 3
    assert hits[0][0].id == "r0"
    assert hits[0][1] >= hits[1][1]

    # Health
    assert store.health() is True

    # Delete all
    n_deleted = store.delete_all()
    assert n_deleted == 10
    assert store.count() == 0


def test_qdrant_smoke_skip_if_unavailable():
    """Skip Qdrant test unless a local Qdrant is reachable."""
    pytest.importorskip("qdrant_client")
    import socket
    s = socket.socket()
    s.settimeout(0.5)
    try:
        s.connect(("localhost", 6333))
    except OSError:
        pytest.skip("Qdrant not running on localhost:6333")
    finally:
        s.close()

    from multimodal_rag.stores.qdrant_store import QdrantStore
    store = QdrantStore(url="http://localhost:6333", collection="test_recipes", dim=128)
    store.delete_all()
    recipes = [_make_recipe(i) for i in range(5)]
    records = [VectorRecord.from_recipe(r, _random_vec(seed=i)) for i, r in enumerate(recipes)]
    store.upsert(records)
    assert store.count() == 5
    hits = store.search(_random_vec(seed=0), top_k=2)
    assert hits[0][0].id == "r0"
    store.delete_all()
