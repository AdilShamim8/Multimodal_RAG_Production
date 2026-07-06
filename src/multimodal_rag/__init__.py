"""Multimodal RAG Production package.

A production-grade implementation of a multimodal Retrieval-Augmented Generation
pipeline (embed → retrieve → rerank → generate) with pluggable model providers
and vector stores.
"""

from multimodal_rag._version import __version__
from multimodal_rag.config import Settings, get_settings

__all__ = ["__version__", "Settings", "get_settings"]
