"""Reranker protocol + provider implementations.

A reranker takes a query and a list of candidate items (text + image pairs)
and produces a more accurate relevance score than first-stage retrieval. The
original notebook uses NVIDIA Llama-Nemotron-Rerank-VL.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy as np
import structlog
from PIL import Image
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from multimodal_rag.config import Settings, get_settings
from multimodal_rag.exceptions import (
    ProviderNotAvailableError,
    RerankerProviderError,
)
from multimodal_rag.monitoring import RERANK_OPS
from multimodal_rag.schemas import Recipe

log = structlog.get_logger(__name__)


@runtime_checkable
class Reranker(Protocol):
    """Rerank candidate recipes given a text query."""

    name: str

    def rerank(
        self,
        query: str,
        candidates: list[Recipe],
        top_k: int | None = None,
    ) -> list[tuple[Recipe, float]]:
        """Return ``(recipe, score)`` pairs sorted by relevance, descending."""


# ---------------------------------------------------------------------------
# Mock reranker
# ---------------------------------------------------------------------------


class MockReranker:
    """Deterministic lexical-overlap reranker.

    Uses token-overlap (Jaccard) between the query and each candidate's title
    + text. Surprisingly effective for short queries and unit tests.
    """

    def __init__(self) -> None:
        self.name = "mock"

    @staticmethod
    def _tokens(s: str) -> set[str]:
        return {t for t in s.lower().split() if len(t) > 2}

    def rerank(
        self,
        query: str,
        candidates: list[Recipe],
        top_k: int | None = None,
    ) -> list[tuple[Recipe, float]]:
        RERANK_OPS.labels(provider="mock").inc()
        q_tokens = self._tokens(query)
        scored: list[tuple[Recipe, float]] = []
        for c in candidates:
            text = (c.title + " " + c.text).lower()
            c_tokens = self._tokens(text)
            if not q_tokens or not c_tokens:
                score = 0.0
            else:
                score = len(q_tokens & c_tokens) / len(q_tokens | c_tokens)
            scored.append((c, float(score)))
        scored.sort(key=lambda x: x[1], reverse=True)
        if top_k is not None:
            scored = scored[:top_k]
        return scored


# ---------------------------------------------------------------------------
# Local HF reranker (NVIDIA Llama-Nemotron-Rerank-VL)
# ---------------------------------------------------------------------------


class LocalHFReranker:
    """NVIDIA Llama-Nemotron-Rerank-VL via transformers.

    Implements the chat-template based rerank protocol described in the model
    card: each (query, candidate) pair is wrapped in a ``[RERANKER]`` prompt
    and the model's next-token logit for ``"yes"`` is used as the score.
    """

    def __init__(self, model_id: str, device: str = "auto") -> None:
        try:
            import torch  # noqa: F401
            from transformers import AutoModelForSequenceClassification, AutoProcessor
        except ImportError as e:  # pragma: no cover
            raise ProviderNotAvailableError(
                "local_hf reranker requires the 'gpu' extra"
            ) from e
        import torch

        self.model_id = model_id
        self.name = "local_hf"
        self.device = torch.device(
            "cuda" if device == "auto" and torch.cuda.is_available() else "cpu"
        ) if device == "auto" else torch.device(device)

        log.info("loading_reranker", model_id=model_id, device=str(self.device))
        self.processor = AutoProcessor.from_pretrained(
            model_id, trust_remote_code=True
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_id,
            trust_remote_code=True,
        ).to(self.device)
        self.model.eval()

    @retry(
        retry=retry_if_exception_type(RerankerProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=8),
        reraise=True,
    )
    def rerank(
        self,
        query: str,
        candidates: list[Recipe],
        top_k: int | None = None,
    ) -> list[tuple[Recipe, float]]:
        import torch

        RERANK_OPS.labels(provider="local_hf").inc()
        scored: list[tuple[Recipe, float]] = []

        try:
            for c in candidates:
                # Build a RERANKER-style prompt per the Nemotron card.
                prompt = (
                    f"[RERANKER]\nQuery: {query}\nDocument: {c.title}. {c.text[:500]}"
                )
                inputs = self.processor(
                    text=prompt, return_tensors="pt", truncation=True, max_length=1024
                ).to(self.device)
                with torch.no_grad():
                    logits = self.model(**inputs).logits
                # Use sigmoid on the "positive" logit as the score.
                score = float(torch.sigmoid(logits.float().squeeze().cpu()))
                scored.append((c, score))
        except Exception as e:
            raise RerankerProviderError(f"local_hf rerank failed: {e}") from e

        scored.sort(key=lambda x: x[1], reverse=True)
        if top_k is not None:
            scored = scored[:top_k]
        return scored


# ---------------------------------------------------------------------------
# OpenAI reranker (LLM-as-judge)
# ---------------------------------------------------------------------------


class OpenAIReranker:
    """LLM-as-judge reranker using OpenAI chat completions.

    Asks the model to score each candidate in ``[0, 1]``. Works on text only;
    images are not sent to the model.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise ProviderNotAvailableError("openai reranker requires OPENAI_API_KEY")
        try:
            import openai
        except ImportError as e:  # pragma: no cover
            raise ProviderNotAvailableError("pip install openai") from e
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.name = "openai"

    @retry(
        retry=retry_if_exception_type(RerankerProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=8),
        reraise=True,
    )
    def rerank(
        self,
        query: str,
        candidates: list[Recipe],
        top_k: int | None = None,
    ) -> list[tuple[Recipe, float]]:
        import json

        RERANK_OPS.labels(provider="openai").inc()
        docs = [
            {"id": i, "title": c.title, "snippet": c.text[:300]}
            for i, c in enumerate(candidates)
        ]
        prompt = (
            "You are a reranker. For each document, return a relevance score in "
            "[0, 1] for the given query. Respond as JSON: "
            '{"scores": [{"id": 0, "score": 0.0}, ...]}\n\n'
            f"Query: {query}\nDocuments: {json.dumps(docs)}"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            scores = {item["id"]: float(item["score"]) for item in data.get("scores", [])}
        except Exception as e:
            raise RerankerProviderError(f"openai rerank failed: {e}") from e

        scored = [(candidates[i], scores.get(i, 0.0)) for i in range(len(candidates))]
        scored.sort(key=lambda x: x[1], reverse=True)
        if top_k is not None:
            scored = scored[:top_k]
        return scored


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_reranker(settings: Settings | None = None) -> Reranker:
    s = settings or get_settings()
    name = s.reranker_provider
    log.info("building_reranker", provider=name)
    if name == "mock":
        return MockReranker()
    if name == "local_hf":
        return LocalHFReranker(model_id=s.reranker_model_id, device=s.model_device)
    if name == "openai":
        return OpenAIReranker(api_key=s.openai_api_key, model=s.openai_reranker_model)
    raise ProviderNotAvailableError(f"unknown reranker provider: {name}")


__all__ = [
    "Reranker",
    "MockReranker",
    "LocalHFReranker",
    "OpenAIReranker",
    "build_reranker",
]

# Keep imports used in type hints
_ = Image, np, Any
