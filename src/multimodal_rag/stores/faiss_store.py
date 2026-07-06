"""FAISS in-memory vector store with optional on-disk index."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import structlog

from multimodal_rag.exceptions import VectorStoreError
from multimodal_rag.schemas import Recipe
from multimodal_rag.stores.base import VectorRecord, VectorStore

log = structlog.get_logger(__name__)


class FAISSStore:
    """In-memory FAISS index with optional on-disk persistence.

    Payloads (recipes) are kept in a Python dict keyed by FAISS-assigned
    integer id. Suitable for single-node deployments up to ~1M vectors.
    """

    def __init__(
        self,
        index_path: str = "./data/faiss/index.faiss",
        dim: int = 2048,
    ) -> None:
        try:
            import faiss  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise VectorStoreError("faiss-cpu not installed") from e

        self._faiss = faiss
        self.dim = dim
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.name = "faiss"

        # We use IndexFlatIP (inner product) on L2-normalised vectors → cosine sim.
        self.index = faiss.IndexFlatIP(dim)
        self._id_to_recipe: dict[int, Recipe] = {}
        self._next_id: int = 0

        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                log.info("faiss_loaded", path=str(self.index_path), n=self.index.ntotal)
            except Exception as e:
                log.warning("faiss_load_failed", error=str(e))

    # ------------------------------------------------------------------
    def upsert(self, records: list[VectorRecord]) -> int:
        if not records:
            return 0
        # NOTE: IndexFlatIP does not support in-place updates; we append and
        # let the search deduplicate by id (last-writer-wins via the dict).
        vecs = np.array([r.vector for r in records], dtype=np.float32)
        # L2-normalise so inner product == cosine similarity
        norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
        vecs = vecs / norms
        self.index.add(vecs)
        for r in records:
            i = self._next_id
            self._next_id += 1
            try:
                self._id_to_recipe[i] = Recipe.model_validate(r.payload)
            except Exception:
                self._id_to_recipe[i] = Recipe(id=r.id, text=str(r.payload))
        # Persist
        try:
            self._faiss.write_index(self.index, str(self.index_path))
        except Exception as e:
            log.warning("faiss_persist_failed", error=str(e))
        return len(records)

    def search(
        self,
        query: np.ndarray,
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[tuple[Recipe, float]]:
        if self.index.ntotal == 0:
            return []
        q = np.asarray(query, dtype=np.float32).reshape(1, -1)
        q = q / (np.linalg.norm(q) + 1e-12)
        scores, indices = self.index.search(q, k=min(top_k, self.index.ntotal))
        out: list[tuple[Recipe, float]] = []
        for sc, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            recipe = self._id_to_recipe.get(int(idx))
            if recipe is None:
                continue
            # Apply metadata filter (post-filter; FAISS has no native filter)
            if filter and not all(recipe.metadata.get(k) == v for k, v in filter.items()):
                continue
            out.append((recipe, float(sc)))
        return out

    def count(self) -> int:
        return int(self.index.ntotal)

    def delete_all(self) -> int:
        n = self.count()
        self.index = self._faiss.IndexFlatIP(self.dim)
        self._id_to_recipe.clear()
        self._next_id = 0
        try:
            if self.index_path.exists():
                self.index_path.unlink()
        except Exception:
            pass
        return n

    def health(self) -> bool:
        return self.index is not None
