"""Shared FastAPI dependencies.

The :func:`get_pipeline` dependency builds the :class:`RAGPipeline` lazily on
first request and caches it for the lifetime of the worker process. Tests can
override this with ``app.dependency_overrides[get_pipeline] = ...``.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from multimodal_rag.config import Settings, get_settings
from multimodal_rag.exceptions import AuthenticationError
from multimodal_rag.pipeline import RAGPipeline, build_rag_pipeline


@lru_cache(maxsize=1)
def _cached_pipeline() -> RAGPipeline:
    return build_rag_pipeline()


def get_pipeline() -> RAGPipeline:
    """Return the process-wide :class:`RAGPipeline` instance."""
    return _cached_pipeline()


def get_settings_dep() -> Settings:
    return get_settings()


def verify_api_key(
    settings: Annotated[Settings, Depends(get_settings_dep)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> str | None:
    """Validate the ``X-API-Key`` header if ``API_KEY`` is configured."""
    if not settings.api_key:
        return None
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing X-API-Key header",
        )
    return x_api_key


# Convenience type aliases for route signatures
PipelineDep = Annotated[RAGPipeline, Depends(get_pipeline)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
ApiKeyDep = Annotated[str | None, Depends(verify_api_key)]

__all__ = [
    "get_pipeline",
    "get_settings_dep",
    "verify_api_key",
    "PipelineDep",
    "SettingsDep",
    "ApiKeyDep",
    "AuthenticationError",
]
