"""Hierarchical exception hierarchy for the multimodal-rag package.

Every domain-specific exception inherits from ``MultimodalRagError`` so callers
can catch the whole family with a single ``except``. The FastAPI error handlers
in ``multimodal_rag/api/middleware.py`` map each leaf class to an HTTP status
code, which keeps API error semantics consistent.
"""

from __future__ import annotations


class MultimodalRagError(Exception):
    """Base class for all package errors."""


# --- Configuration ---------------------------------------------------------
class ConfigError(MultimodalRagError):
    """Raised when configuration is missing or invalid."""


# --- Providers -------------------------------------------------------------
class ProviderError(MultimodalRagError):
    """Base class for all model-provider errors."""


class EmbeddingProviderError(ProviderError):
    """Raised when an embedding provider fails."""


class RerankerProviderError(ProviderError):
    """Raised when a reranker provider fails."""


class GeneratorProviderError(ProviderError):
    """Raised when a generator provider fails."""


class ProviderNotAvailableError(ProviderError):
    """Raised when a requested provider name is unknown or its deps are missing."""


# --- Vector store ----------------------------------------------------------
class VectorStoreError(MultimodalRagError):
    """Base class for all vector-store errors."""


class VectorStoreConnectionError(VectorStoreError):
    """Raised when the vector store cannot be reached."""


class VectorStoreWriteError(VectorStoreError):
    """Raised when a write to the vector store fails."""


class CollectionNotFoundError(VectorStoreError):
    """Raised when a query targets a non-existent collection."""


# --- Pipeline --------------------------------------------------------------
class PipelineError(MultimodalRagError):
    """Base class for RAG pipeline orchestration errors."""


class RetrievalError(PipelineError):
    """Raised when retrieval from the vector store fails."""


class RerankError(PipelineError):
    """Raised when the reranker step fails."""


class GenerationError(PipelineError):
    """Raised when the generator step fails."""


# --- Data ------------------------------------------------------------------
class DatasetError(MultimodalRagError):
    """Raised when the dataset cannot be loaded or is malformed."""


# --- API -------------------------------------------------------------------
class AuthenticationError(MultimodalRagError):
    """Raised when API authentication fails."""


class RateLimitExceededError(MultimodalRagError):
    """Raised when a client exceeds the rate limit."""


class ValidationError(MultimodalRagError):
    """Raised when request payload validation fails (beyond pydantic)."""
