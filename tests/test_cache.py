"""Tests for the cache module."""

from __future__ import annotations

import os

# Force-enable the cache for this module (conftest disables it globally).
os.environ["CACHE_ENABLED"] = "true"
os.environ["CACHE_MAX_SIZE"] = "64"

import importlib

import multimodal_rag.cache as cache_mod
import multimodal_rag.config as config_mod

config_mod.get_settings.cache_clear()
importlib.reload(cache_mod)

from multimodal_rag.cache import cached, clear_cache  # noqa: E402


def test_cached_returns_same_result():
    calls = {"n": 0}

    @cached(prefix="test")
    def expensive(x: int) -> int:
        calls["n"] += 1
        return x * 2

    assert expensive(3) == 6
    assert expensive(3) == 6
    assert calls["n"] == 1
    assert expensive(4) == 8
    assert calls["n"] == 2
    clear_cache()
