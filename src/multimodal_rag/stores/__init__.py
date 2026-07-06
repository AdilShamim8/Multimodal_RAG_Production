"""Vector store subpackage.

Exposes the :class:`VectorStore` protocol and a :func:`build_vector_store`
factory. Three implementations are provided:

* :class:`ChromaStore`   — embedded, file-backed, no extra services needed
* :class:`QdrantStore`   — production-grade, runs as a separate service
* :class:`FAISSStore`    — in-memory with optional on-disk index
"""

from multimodal_rag.stores.base import VectorStore, VectorRecord
from multimodal_rag.stores.factory import build_vector_store

__all__ = ["VectorStore", "VectorRecord", "build_vector_store"]
