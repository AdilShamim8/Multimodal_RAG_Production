"""In-memory LRU cache + optional Redis backend.

The default cache is an in-process :class:`cachetools.LRUCache`. The FastAPI
app uses :func:`cached` as a decorator on expensive pure-ish functions
(e.g. embedding the same query twice in a minute).
"""

from __future__ import annotations

import functools
import hashlib
import json
from collections.abc import Callable
from typing import Any

from cachetools import LRUCache

from multimodal_rag.config import get_settings

_CACHE: LRUCache | None = None


def _get_cache() -> LRUCache:
    global _CACHE
    if _CACHE is None:
        s = get_settings()
        _CACHE = LRUCache(maxsize=s.cache_max_size)
    return _CACHE


def _make_key(*args: Any, **kwargs: Any) -> str:
    """Stable hash key from positional + keyword args."""
    payload = json.dumps({"args": repr(args), "kwargs": repr(kwargs)}, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def cached(prefix: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator: memoize a function under ``prefix:<hash>`` for cache TTL.

    Args:
        prefix: Namespace key (e.g. ``"embed"``) to keep caches organised.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        s = get_settings()
        if not s.cache_enabled:
            return fn

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = _get_cache()
            key = f"{prefix}:{_make_key(*args, **kwargs)}"
            if key in cache:
                return cache[key]
            result = fn(*args, **kwargs)
            cache[key] = result
            return result

        wrapper.cache_clear = _get_cache().clear  # type: ignore[attr-defined]
        return wrapper

    return decorator


def clear_cache() -> None:
    """Drop every cached entry (used by tests and ``/admin/cache/clear``)."""
    if _CACHE is not None:
        _CACHE.clear()
