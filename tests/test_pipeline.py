"""Tests for the RAG pipeline orchestrator."""

from __future__ import annotations

import pytest
from PIL import Image

from multimodal_rag.exceptions import ValidationError


def test_pipeline_retrieve_text(pipeline):
    out = pipeline.retrieve(query_text="tomato pasta", top_k=3)
    assert len(out) == 3
    assert all(r.score >= 0.0 for r in out)
    assert out[0].rank == 1


def test_pipeline_retrieve_image(pipeline):
    img = Image.new("RGB", (32, 32), color=(255, 0, 0))
    out = pipeline.retrieve(query_image=img, top_k=2)
    assert len(out) == 2


def test_pipeline_retrieve_text_and_image(pipeline):
    img = Image.new("RGB", (32, 32))
    out = pipeline.retrieve(query_text="garlic", query_image=img, top_k=2)
    assert len(out) == 2


def test_pipeline_requires_query(pipeline):
    with pytest.raises(ValidationError):
        pipeline.retrieve()


def test_pipeline_rerank(pipeline):
    retrieved = pipeline.retrieve(query_text="tomato", top_k=5)
    reranked = pipeline.rerank(query_text="tomato", candidates=retrieved, top_k=3)
    assert len(reranked) <= 3
    assert reranked[0].score >= reranked[-1].score


def test_pipeline_generate(pipeline):
    retrieved = pipeline.retrieve(query_text="tomato", top_k=3)
    text = pipeline.generate("tomato", [r.recipe for r in retrieved])
    assert isinstance(text, str)
    assert len(text) > 0


def test_pipeline_run_full(pipeline):
    out = pipeline.run(query_text="tomato basil", top_k=3, rerank=True, generate=True)
    assert "retrieved" in out
    assert "reranked" in out
    assert "summary" in out
    assert "timings" in out
    assert "total" in out["timings"]
    assert out["providers"]["embedding"] == "mock"


def test_pipeline_run_no_rerank_no_generate(pipeline):
    out = pipeline.run(query_text="soup", top_k=3, rerank=False, generate=False)
    assert out["reranked"] is None
    assert out["summary"] is None


def test_pipeline_ingest_more(pipeline):
    from multimodal_rag.schemas import Recipe

    new_recipes = [
        Recipe(id=f"new-{i}", title=f"New {i}", text=f"text {i}") for i in range(5)
    ]
    n = pipeline.ingest(new_recipes)
    assert n == 5
