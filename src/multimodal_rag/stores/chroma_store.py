"""Chroma embedded vector store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import structlog

from multimodal_rag.exceptions import VectorStoreError
from multimodal_rag.schemas import Recipe
from multimodal_rag.stores.base import VectorRecord, VectorStore

log = structlog.get_logger(__name__)


def _flatten_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested dict/list values so Chroma accepts them.

    Chroma only accepts str/int/float/bool/None (or lists of those) at the
    top level. We promote nested ``metadata`` keys to top-level dotted keys
    and JSON-encode any complex values.
    """
    import json

    flat: dict[str, Any] = {}
    for k, v in payload.items():
        if k == "metadata" and isinstance(v, dict):
            for mk, mv in v.items():
                if isinstance(mv, (str, int, float, bool)) or mv is None:
                    flat[f"meta_{mk}"] = mv
                elif isinstance(mv, list) and all(
                    isinstance(x, (str, int, float, bool)) for x in mv
                ):
                    flat[f"meta_{mk}"] = mv
                else:
                    flat[f"meta_{mk}"] = json.dumps(mv, default=str)
        elif isinstance(v, (str, int, float, bool)) or v is None:
            flat[k] = v
        elif isinstance(v, list) and all(
            isinstance(x, (str, int, float, bool)) for x in v
        ):
            flat[k] = v
        else:
            flat[k] = json.dumps(v, default=str)
    return flat


def _unflatten_metadata(flat: dict[str, Any]) -> dict[str, Any]:
    """Reverse of :func:`_flatten_metadata` (best effort)."""
    import json

    out: dict[str, Any] = {}
    nested: dict[str, Any] = {}
    for k, v in flat.items():
        if k.startswith("meta_"):
            mk = k[5:]
            if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                try:
                    nested[mk] = json.loads(v)
                    continue
                except Exception:
                    pass
            nested[mk] = v
        else:
            out[k] = v
    if nested:
        out["metadata"] = nested
    return out


class ChromaStore:
    """File-backed Chroma store. No external services required."""

    def __init__(self, persist_dir: str, collection: str = "recipes") -> None:
        try:
            import chromadb
        except ImportError as e:  # pragma: no cover
            raise VectorStoreError("chromadb not installed") from e

        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = collection
        self.collection = self.client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )
        self.name = "chroma"
        log.info("chroma_ready", persist_dir=persist_dir, collection=collection)

    def upsert(self, records: list[VectorRecord]) -> int:
        if not records:
            return 0
        self.collection.upsert(
            ids=[r.id for r in records],
            embeddings=[r.vector for r in records],
            metadatas=[_flatten_metadata(r.payload) for r in records],
        )
        return len(records)

    def search(
        self,
        query: np.ndarray,
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[tuple[Recipe, float]]:
        q = query.astype(float).tolist() if isinstance(query, np.ndarray) else query
        res = self.collection.query(
            query_embeddings=[q],
            n_results=top_k,
            where=filter,
        )
        out: list[tuple[Recipe, float]] = []
        ids = (res.get("ids") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        for i, _id in enumerate(ids):
            meta = _unflatten_metadata(metas[i]) if i < len(metas) else {}
            # Chroma returns cosine *distance* (lower = closer); convert to similarity
            dist = float(dists[i]) if i < len(dists) else 1.0
            score = 1.0 - dist
            try:
                recipe = Recipe.model_validate(meta)
            except Exception:  # pragma: no cover
                recipe = Recipe(id=str(_id), text=str(meta))
            out.append((recipe, score))
        return out

    def count(self) -> int:
        try:
            return self.collection.count()
        except Exception:
            return 0

    def delete_all(self) -> int:
        n = self.count()
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        return n

    def health(self) -> bool:
        try:
            self.count()
            return True
        except Exception:
            return False
