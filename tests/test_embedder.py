"""Tests for the embedder providers."""

from __future__ import annotations

import numpy as np
from PIL import Image

from multimodal_rag.models.embedder import (
    MockEmbedder,
    build_embedder,
)


def test_mock_embedder_dim():
    e = MockEmbedder(dim=128)
    assert e.dim == 128
    v = e.embed_text("hello")
    assert v.shape == (128,)
    assert v.dtype == np.float32


def test_mock_embedder_deterministic():
    e = MockEmbedder(dim=64)
    a = e.embed_text("tomato pasta")
    b = e.embed_text("tomato pasta")
    c = e.embed_text("different")
    assert np.allclose(a, b)
    assert not np.allclose(a, c)


def test_mock_embedder_l2_normalised():
    e = MockEmbedder(dim=128)
    v = e.embed_text("recipe with garlic")
    assert abs(np.linalg.norm(v) - 1.0) < 1e-5


def test_mock_embedder_image():
    e = MockEmbedder(dim=128)
    img = Image.new("RGB", (32, 32), color=(255, 0, 0))
    v = e.embed_image(img)
    assert v.shape == (128,)
    assert abs(np.linalg.norm(v) - 1.0) < 1e-5


def test_mock_embedder_batch():
    e = MockEmbedder(dim=128)
    img = Image.new("RGB", (16, 16))
    items = [{"text": "a"}, {"text": "b", "image": img}, {"image": img}]
    out = e.embed_batch(items)
    assert out.shape == (3, 128)


def test_build_embedder_returns_mock_by_default():
    e = build_embedder()
    assert e.name == "mock"


def test_unknown_provider_raises():
    from multimodal_rag.config import Settings
    from multimodal_rag.exceptions import ProviderNotAvailableError
    import pytest
    from pydantic import ValidationError as PydanticValidationError

    # Settings with an invalid provider is rejected at the schema level;
    # otherwise the factory raises ProviderNotAvailableError.
    with pytest.raises((ProviderNotAvailableError, PydanticValidationError)):
        s = Settings(embedding_provider="bogus", cors_origins="*")  # type: ignore[call-arg]
        build_embedder(s)
