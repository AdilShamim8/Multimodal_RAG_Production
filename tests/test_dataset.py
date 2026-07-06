"""Tests for the dataset loader."""

from __future__ import annotations

import pytest

from multimodal_rag.data import build_dataset_loader
from multimodal_rag.exceptions import DatasetError


def test_load_sample():
    loader = build_dataset_loader()
    recipes = loader.load(source="sample", limit=10)
    assert len(recipes) == 10
    assert all(r.id for r in recipes)


def test_load_sample_default_size():
    loader = build_dataset_loader()
    recipes = loader.load(source="sample")
    assert len(recipes) == 200


def test_recipe_fields():
    loader = build_dataset_loader()
    recipes = loader.load(source="sample", limit=1)
    r = recipes[0]
    assert r.id
    assert r.title
    assert r.text
    assert r.image_url


def test_load_unknown_source():
    loader = build_dataset_loader()
    with pytest.raises(DatasetError):
        loader.load(source="bogus")


def test_stream_sample():
    loader = build_dataset_loader()
    n = sum(1 for _ in loader.stream(source="sample", limit=5))
    assert n == 5
