"""Tests for the generator providers."""

from __future__ import annotations

import pytest

from multimodal_rag.models.generator import MockGenerator, build_generator, build_prompt
from multimodal_rag.schemas import Recipe


def _make(title: str, text: str = "ingredients: tomato, garlic, basil") -> Recipe:
    return Recipe(id=title.lower().replace(" ", "-"), title=title, text=text)


def test_mock_generator_returns_string():
    g = MockGenerator()
    out = g.generate("tomato", [_make("Pasta"), _make("Salad")])
    assert isinstance(out, str)
    assert "Pasta" in out or "pasta" in out.lower() or "mock" in out.lower()


def test_mock_generator_handles_empty_recipes():
    g = MockGenerator()
    out = g.generate("nothing", [])
    assert "No recipes" in out


def test_build_prompt_includes_query_and_recipes():
    p = build_prompt("pasta", [_make("Pasta", "tomato garlic")], "summary")
    assert "pasta" in p.lower()
    assert "Pasta" in p
    assert "tomato" in p.lower()


def test_build_prompt_styles():
    for style in ("summary", "comparison", "recipe_card"):
        p = build_prompt("x", [_make("A")], style)
        assert style in p.lower() or "recipe" in p.lower()


def test_build_generator_returns_mock():
    g = build_generator()
    assert g.name == "mock"


def test_unknown_generator_raises():
    from multimodal_rag.config import Settings
    from multimodal_rag.exceptions import ProviderNotAvailableError
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises((ProviderNotAvailableError, PydanticValidationError)):
        s = Settings(generator_provider="bogus", cors_origins="*")  # type: ignore[call-arg]
        build_generator(s)
