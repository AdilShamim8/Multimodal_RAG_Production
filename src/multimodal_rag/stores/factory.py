"""VectorStore factory."""

from __future__ import annotations

import structlog

from multimodal_rag.config import Settings, get_settings
from multimodal_rag.exceptions import VectorStoreError
from multimodal_rag.stores.base import VectorStore

log = structlog.get_logger(__name__)


def build_vector_store(settings: Settings | None = None) -> VectorStore:
    """Return the configured :class:`VectorStore` implementation."""
    s = settings or get_settings()
    name = s.vector_store
    log.info("building_vector_store", store=name, dim=s.embeddings_dim)

    if name == "chroma":
        from multimodal_rag.stores.chroma_store import ChromaStore
        return ChromaStore(persist_dir=s.chroma_persist_dir, collection="recipes")
    if name == "qdrant":
        from multimodal_rag.stores.qdrant_store import QdrantStore
        return QdrantStore(
            url=s.qdrant_url,
            api_key=s.qdrant_api_key,
            collection=s.qdrant_collection,
            dim=s.embeddings_dim,
        )
    if name == "faiss":
        from multimodal_rag.stores.faiss_store import FAISSStore
        return FAISSStore(index_path=s.faiss_index_path, dim=s.embeddings_dim)
    raise VectorStoreError(f"unknown vector store: {name}")
