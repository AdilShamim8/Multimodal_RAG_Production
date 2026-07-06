"""Qdrant vector store client."""

from __future__ import annotations

from typing import Any

import numpy as np
import structlog

from multimodal_rag.exceptions import VectorStoreConnectionError, VectorStoreError
from multimodal_rag.schemas import Recipe
from multimodal_rag.stores.base import VectorRecord, VectorStore

log = structlog.get_logger(__name__)


class QdrantStore:
    """Qdrant vector store. Requires a running Qdrant instance."""

    def __init__(
        self,
        url: str,
        collection: str = "recipes",
        api_key: str = "",
        dim: int = 2048,
    ) -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.exceptions import UnexpectedResponse
            from qdrant_client.http.models import (
                Distance,
                VectorParams,
            )
        except ImportError as e:  # pragma: no cover
            raise VectorStoreError("qdrant-client not installed") from e

        self._UnexpectedResponse = UnexpectedResponse
        self.collection_name = collection
        self.dim = dim
        try:
            self.client = QdrantClient(url=url, api_key=api_key or None)
            try:
                self.client.get_collection(collection)
            except UnexpectedResponse:
                self.client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
                )
                log.info("qdrant_collection_created", collection=collection)
        except Exception as e:
            raise VectorStoreConnectionError(f"cannot reach Qdrant at {url}: {e}") from e

        self.name = "qdrant"
        log.info("qdrant_ready", url=url, collection=collection)

    def upsert(self, records: list[VectorRecord]) -> int:
        if not records:
            return 0
        from qdrant_client.http.models import PointStruct

        points = [
            PointStruct(id=r.id, vector=r.vector, payload=r.payload)
            for r in records
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def search(
        self,
        query: np.ndarray,
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[tuple[Recipe, float]]:
        from qdrant_client.http.models import Filter

        q = query.astype(float).tolist() if isinstance(query, np.ndarray) else query
        qfilter = Filter(must=filter) if filter else None
        try:
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=q,
                limit=top_k,
                query_filter=qfilter,
            )
        except Exception as e:
            raise VectorStoreError(f"qdrant search failed: {e}") from e

        out: list[tuple[Recipe, float]] = []
        for hit in hits:
            try:
                recipe = Recipe.model_validate(hit.payload or {})
            except Exception:
                recipe = Recipe(id=str(hit.id), text=str(hit.payload))
            out.append((recipe, float(hit.score)))
        return out

    def count(self) -> int:
        try:
            r = self.client.count(collection_name=self.collection_name)
            return r.count
        except Exception:
            return 0

    def delete_all(self) -> int:
        n = self.count()
        self.client.delete_collection(self.collection_name)
        from qdrant_client.http.models import Distance, VectorParams
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
        )
        return n

    def health(self) -> bool:
        try:
            self.client.get_collection(self.collection_name)
            return True
        except Exception:
            return False
