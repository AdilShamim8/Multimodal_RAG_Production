"""API routes subpackage."""

from multimodal_rag.api.routes import (
    generate,
    health,
    ingest,
    rag,
    rerank,
    retrieve,
)

__all__ = ["health", "ingest", "retrieve", "rerank", "generate", "rag"]
