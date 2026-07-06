"""RAG pipeline orchestrator.

The :class:`RAGPipeline` ties together the embedder, vector store, reranker,
and generator into a single ``run()`` call. Each stage is timed and exposed
in the response so callers (API / CLI) can surface latency to users.
"""

from __future__ import annotations

import base64
import io
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import numpy as np
import structlog
from PIL import Image

from multimodal_rag.config import Settings, get_settings
from multimodal_rag.exceptions import (
    PipelineError,
    RetrievalError,
    ValidationError,
)
from multimodal_rag.models import (
    Embedder,
    Generator,
    Reranker,
    build_embedder,
    build_generator,
    build_reranker,
)
from multimodal_rag.monitoring import PIPELINE_STAGE_LATENCY
from multimodal_rag.schemas import (
    Recipe,
    RecipeWithScore,
)
from multimodal_rag.stores import VectorStore, build_vector_store

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_image_from_field(query_image: str) -> Image.Image:
    """Decode a query image from a base64 data URL or http(s) URL."""
    if query_image.startswith("data:"):
        # data:image/png;base64,XXXX
        try:
            header, b64 = query_image.split(",", 1)
            raw = base64.b64decode(b64)
            return Image.open(io.BytesIO(raw))
        except Exception as e:
            raise ValidationError(f"invalid base64 image: {e}") from e
    parsed = urlparse(query_image)
    if parsed.scheme in ("http", "https"):
        try:
            import httpx

            resp = httpx.get(query_image, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            return Image.open(io.BytesIO(resp.content))
        except Exception as e:
            raise ValidationError(f"cannot fetch image: {e}") from e
    raise ValidationError(f"unsupported image reference: {query_image[:80]}")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


@dataclass
class RAGPipeline:
    """End-to-end RAG orchestrator.

    Holds single instances of the embedder, vector store, reranker, and
    generator for its lifetime. ``run()`` is the entry point.
    """

    embedder: Embedder
    store: VectorStore
    reranker: Reranker
    generator: Generator
    settings: Settings = field(default_factory=get_settings)

    # ------------------------------------------------------------------
    def ingest(self, recipes: list[Recipe], batch_size: int | None = None) -> int:
        """Embed + upsert recipes into the vector store.

        Returns the number of records written.
        """
        bs = batch_size or self.settings.embedding_batch_size
        total = 0
        for i in range(0, len(recipes), bs):
            chunk = recipes[i : i + bs]
            items = [{"text": r.text, "image": None} for r in chunk]
            vecs = self.embedder.embed_batch(items)
            from multimodal_rag.stores.base import VectorRecord

            records = [
                VectorRecord.from_recipe(r, v)
                for r, v in zip(chunk, vecs)
                if np.linalg.norm(v) > 1e-6
            ]
            total += self.store.upsert(records)
            log.info("ingest_chunk", index=i, size=len(chunk), total=total)
        return total

    # ------------------------------------------------------------------
    def retrieve(
        self,
        *,
        query_text: str | None = None,
        query_image: Image.Image | None = None,
        top_k: int | None = None,
    ) -> list[RecipeWithScore]:
        """Embed the query and retrieve ``top_k`` candidates from the store."""
        if not query_text and query_image is None:
            raise ValidationError("at least one of query_text or query_image is required")

        t0 = time.perf_counter()
        try:
            if query_image is not None and query_text:
                v_text = self.embedder.embed_text(query_text)
                v_img = self.embedder.embed_image(query_image)
                vec = 0.5 * v_text + 0.5 * v_img
                vec = vec / (np.linalg.norm(vec) + 1e-12)
            elif query_image is not None:
                vec = self.embedder.embed_image(query_image)
            else:
                vec = self.embedder.embed_text(query_text or "")
        except Exception as e:
            raise RetrievalError(f"embedding failed: {e}") from e

        try:
            hits = self.store.search(vec, top_k=top_k or self.settings.default_top_k)
        except Exception as e:
            raise RetrievalError(f"vector store search failed: {e}") from e

        dt = time.perf_counter() - t0
        PIPELINE_STAGE_LATENCY.labels(stage="retrieve").observe(dt)
        return [
            RecipeWithScore(recipe=recipe, score=score, rank=i + 1)
            for i, (recipe, score) in enumerate(hits)
        ]

    # ------------------------------------------------------------------
    def rerank(
        self,
        query_text: str,
        candidates: list[RecipeWithScore],
        top_k: int | None = None,
    ) -> list[RecipeWithScore]:
        """Re-score candidates with the reranker."""
        if not candidates:
            return []
        t0 = time.perf_counter()
        try:
            scored = self.reranker.rerank(
                query=query_text,
                candidates=[c.recipe for c in candidates],
                top_k=top_k or self.settings.rerank_top_k,
            )
        except Exception as e:
            raise RetrievalError(f"rerank failed: {e}") from e
        dt = time.perf_counter() - t0
        PIPELINE_STAGE_LATENCY.labels(stage="rerank").observe(dt)
        return [
            RecipeWithScore(recipe=recipe, score=score, rank=i + 1)
            for i, (recipe, score) in enumerate(scored)
        ]

    # ------------------------------------------------------------------
    def generate(
        self,
        query: str,
        recipes: list[Recipe],
        *,
        style: str = "summary",
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate a summary over the supplied recipes."""
        t0 = time.perf_counter()
        text = self.generator.generate(
            query=query,
            recipes=recipes,
            style=style,
            max_new_tokens=max_new_tokens or self.settings.generate_max_new_tokens,
            temperature=temperature if temperature is not None else self.settings.generate_temperature,
        )
        PIPELINE_STAGE_LATENCY.labels(stage="generate").observe(time.perf_counter() - t0)
        return text

    # ------------------------------------------------------------------
    def run(
        self,
        *,
        query_text: str | None = None,
        query_image: Image.Image | None = None,
        top_k: int | None = None,
        rerank: bool = True,
        rerank_top_k: int | None = None,
        generate: bool = True,
        generate_style: str = "summary",
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Run the full RAG pipeline and return timings + outputs."""
        t0 = time.perf_counter()
        timings: dict[str, float] = {}
        providers = {
            "embedding": self.embedder.name,
            "reranker": self.reranker.name,
            "generator": self.generator.name,
            "vector_store": self.store.name,
        }

        # 1. Retrieve
        retrieved = self.retrieve(
            query_text=query_text,
            query_image=query_image,
            top_k=top_k,
        )
        timings["retrieve"] = time.perf_counter() - t0

        # 2. Rerank
        reranked: list[RecipeWithScore] | None = None
        if rerank and retrieved:
            t1 = time.perf_counter()
            reranked = self.rerank(
                query_text=query_text or "",
                candidates=retrieved,
                top_k=rerank_top_k,
            )
            timings["rerank"] = time.perf_counter() - t1

        # 3. Generate
        summary: str | None = None
        if generate:
            t1 = time.perf_counter()
            context = reranked or retrieved
            summary = self.generate(
                query=query_text or "",
                recipes=[c.recipe for c in context[:10]],
                style=generate_style,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
            )
            timings["generate"] = time.perf_counter() - t1

        timings["total"] = time.perf_counter() - t0
        return {
            "retrieved": retrieved,
            "reranked": reranked,
            "summary": summary,
            "timings": timings,
            "providers": providers,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_rag_pipeline(settings: Settings | None = None) -> RAGPipeline:
    """Wire up all providers and return a ready-to-use :class:`RAGPipeline`."""
    s = settings or get_settings()
    log.info(
        "building_rag_pipeline",
        embedding=s.embedding_provider,
        reranker=s.reranker_provider,
        generator=s.generator_provider,
        vector_store=s.vector_store,
    )
    return RAGPipeline(
        embedder=build_embedder(s),
        store=build_vector_store(s),
        reranker=build_reranker(s),
        generator=build_generator(s),
        settings=s,
    )


__all__ = ["RAGPipeline", "build_rag_pipeline", "_load_image_from_field"]

_ = PipelineError  # keep import in scope for downstream type checks
