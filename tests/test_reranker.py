"""Tests for the reranker providers."""

from __future__ import annotations

import pytest

from multimodal_rag.models.reranker import MockReranker, build_reranker
from multimodal_rag.schemas import Recipe


def _make(title: str, text: str = "") -> Recipe:
    return Recipe(id=title.lower().replace(" ", "-"), title=title, text=text)


def test_mock_reranker_orders_by_overlap():
    r = MockReranker()
    q = "tomato basil pasta"
    cands = [
        _make("Beef Tacos", "mexican beef tacos"),
        _make("Tomato Basil Pasta", "italian pasta with tomato and basil"),
        _make("Sushi Platter", "japanese raw fish"),
    ]
    ranked = r.rerank(q, cands)
    assert ranked[0][0].title == "Tomato Basil Pasta"
    assert ranked[0][1] > ranked[-1][1]


def test_mock_reranker_top_k():
    r = MockReranker()
    cands = [_make(f"Recipe {i}", f"tomato {i}") for i in range(10)]
    ranked = r.rerank("tomato", cands, top_k=3)
    assert len(ranked) == 3


def test_mock_reranker_empty_query():
    r = MockReranker()
    cands = [_make("X", "y")]
    ranked = r.rerank("", cands)
    assert ranked[0][1] == 0.0


def test_build_reranker_returns_mock():
    r = build_reranker()
    assert r.name == "mock"


def test_unknown_reranker_raises():
    from multimodal_rag.config import Settings
    from multimodal_rag.exceptions import ProviderNotAvailableError
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises((ProviderNotAvailableError, PydanticValidationError)):
        s = Settings(reranker_provider="bogus", cors_origins="*")  # type: ignore[call-arg]
        build_reranker(s)
