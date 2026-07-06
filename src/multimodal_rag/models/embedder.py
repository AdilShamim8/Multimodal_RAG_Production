"""Embedder protocol + provider implementations.

The embedder converts a text string and/or a PIL image into a fixed-size
float vector. Three providers are supported:

* ``mock``   — deterministic hash-based vectors (no deps, runs on CPU)
* ``local_hf``— NVIDIA Nemotron-Embed-VL via ``transformers``
* ``openai`` — OpenAI ``text-embedding-3-large`` via the OpenAI API
"""

from __future__ import annotations

import base64
import hashlib
import io
import struct
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
    EmbeddingProviderError,
    ProviderNotAvailableError,
)
from multimodal_rag.monitoring import EMBEDDING_OPS

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Embedder(Protocol):
    """Embed text and/or images into a shared vector space."""

    dim: int

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string into a 1-D float32 vector of length ``dim``."""

    def embed_image(self, image: Image.Image) -> np.ndarray:
        """Embed a single PIL image into a 1-D float32 vector of length ``dim``."""

    def embed_batch(
        self, items: list[dict[str, Any]]
    ) -> np.ndarray:
        """Embed a batch of items.

        Each item is a dict that may contain ``text`` and/or ``image`` (a PIL
        Image). Returns a ``(N, dim)`` float32 array.
        """


# ---------------------------------------------------------------------------
# Mock provider — deterministic, no external deps
# ---------------------------------------------------------------------------


class MockEmbedder:
    """Deterministic hash-based embedder.

    Useful for unit tests and for booting the API on CPU without downloading
    multi-GB model weights. The embedding of any (text, image) pair is the
    SHA-256 hash truncated to ``dim`` floats, L2-normalised.
    """

    def __init__(self, dim: int = 2048, seed: int = 42) -> None:
        self.dim = dim
        self.seed = seed
        self.name = "mock"

    def _hash(self, payload: bytes) -> np.ndarray:
        h = hashlib.sha256(payload + struct.pack(">I", self.seed)).digest()
        # Repeat hash to fill `dim` bytes
        buf = bytearray(h)
        while len(buf) < self.dim * 4:
            buf.extend(hashlib.sha256(bytes(buf[-32:])).digest())
        arr = np.frombuffer(bytes(buf[: self.dim * 4]), dtype=np.uint32).astype(
            np.float32
        )
        # Map to [-1, 1]
        arr = (arr / 2**32 - 0.5) * 2
        # L2-normalise so cosine similarity is well-defined
        norm = np.linalg.norm(arr) + 1e-12
        return (arr / norm).astype(np.float32)

    def embed_text(self, text: str) -> np.ndarray:
        EMBEDDING_OPS.labels(provider="mock", kind="text").inc()
        return self._hash(text.encode("utf-8"))

    def embed_image(self, image: Image.Image) -> np.ndarray:
        EMBEDDING_OPS.labels(provider="mock", kind="image").inc()
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="PNG")
        return self._hash(buf.getvalue())

    def embed_batch(self, items: list[dict[str, Any]]) -> np.ndarray:
        EMBEDDING_OPS.labels(provider="mock", kind="batch").inc()
        out = np.zeros((len(items), self.dim), dtype=np.float32)
        for i, item in enumerate(items):
            text = item.get("text", "")
            img = item.get("image")
            if img is not None:
                v = self.embed_image(img)
                if text:
                    v = 0.5 * v + 0.5 * self.embed_text(text)
                    v = v / (np.linalg.norm(v) + 1e-12)
                out[i] = v
            else:
                out[i] = self.embed_text(text)
        return out


# ---------------------------------------------------------------------------
# Local HuggingFace provider (NVIDIA Nemotron-Embed-VL)
# ---------------------------------------------------------------------------


class LocalHFEmbedder:
    """Loads NVIDIA Nemotron-Embed-VL (or any compatible HF model) on demand.

    Heavy imports (``torch``, ``transformers``) are deferred to ``__init__`` so
    that the mock provider can be used without those packages installed.
    """

    def __init__(
        self,
        model_id: str,
        device: str = "auto",
        torch_dtype: str = "auto",
    ) -> None:
        try:
            import torch  # noqa: F401
            from transformers import AutoModel, AutoProcessor
        except ImportError as e:  # pragma: no cover — depends on env
            raise ProviderNotAvailableError(
                "local_hf embedder requires the 'gpu' extra: pip install -e '.[gpu]'"
            ) from e

        import torch

        self.model_id = model_id
        self.name = "local_hf"
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)

        dtype_map = {
            "auto": torch.float16 if self.device.type == "cuda" else torch.float32,
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        self.dtype = dtype_map[torch_dtype]

        log.info(
            "loading_embedder",
            model_id=model_id,
            device=str(self.device),
            dtype=str(self.dtype),
        )
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(
            model_id,
            torch_dtype=self.dtype,
            trust_remote_code=True,
        ).to(self.device)
        self.model.eval()

        # The Nemotron-Embed-VL hidden size; fall back to 2048
        self.dim = getattr(self.model.config, "hidden_size", 2048)

    @retry(
        retry=retry_if_exception_type(EmbeddingProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=8),
        reraise=True,
    )
    def _embed(self, texts: list[str], images: list[Image.Image | None]) -> np.ndarray:
        import torch

        try:
            inputs = self.processor(
                text=texts, images=images, return_tensors="pt", padding=True
            ).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            emb = outputs.last_hidden_state.mean(dim=1).float().cpu().numpy()
            emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)
            return emb.astype(np.float32)
        except Exception as e:
            raise EmbeddingProviderError(f"local_hf embed failed: {e}") from e

    def embed_text(self, text: str) -> np.ndarray:
        EMBEDDING_OPS.labels(provider="local_hf", kind="text").inc()
        return self._embed([text], [None])[0]

    def embed_image(self, image: Image.Image) -> np.ndarray:
        EMBEDDING_OPS.labels(provider="local_hf", kind="image").inc()
        return self._embed([""], [image])[0]

    def embed_batch(self, items: list[dict[str, Any]]) -> np.ndarray:
        EMBEDDING_OPS.labels(provider="local_hf", kind="batch").inc()
        texts = [it.get("text", "") for it in items]
        imgs = [it.get("image") for it in items]
        return self._embed(texts, imgs)


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------


class OpenAIEmbedder:
    """OpenAI ``text-embedding-3-large`` (3072-dim) — or any other OpenAI model."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        timeout: int = 30,
    ) -> None:
        if not api_key:
            raise ProviderNotAvailableError(
                "openai embedder requires OPENAI_API_KEY to be set"
            )
        try:
            import openai
        except ImportError as e:  # pragma: no cover
            raise ProviderNotAvailableError(
                "openai embedder requires the 'openai' package: pip install openai"
            ) from e
        self.client = openai.OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.name = "openai"
        # text-embedding-3-large = 3072; small = 1536; ada = 1536
        self.dim = 3072 if "large" in model else 1536

    @retry(
        retry=retry_if_exception_type(EmbeddingProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=8),
        reraise=True,
    )
    def _call(self, texts: list[str]) -> np.ndarray:
        try:
            resp = self.client.embeddings.create(model=self.model, input=texts)
            arr = np.array([d.embedding for d in resp.data], dtype=np.float32)
            arr = arr / (np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12)
            return arr
        except Exception as e:
            raise EmbeddingProviderError(f"openai embed failed: {e}") from e

    def embed_text(self, text: str) -> np.ndarray:
        EMBEDDING_OPS.labels(provider="openai", kind="text").inc()
        return self._call([text])[0]

    def embed_image(self, image: Image.Image) -> np.ndarray:
        # OpenAI embeddings are text-only — fall back to a caption-like text
        # derived from the image size + mode. This is intentionally weak; use
        # the local_hf provider for real image embeddings.
        EMBEDDING_OPS.labels(provider="openai", kind="image").inc()
        return self.embed_text(f"image {image.size} {image.mode}")

    def embed_batch(self, items: list[dict[str, Any]]) -> np.ndarray:
        EMBEDDING_OPS.labels(provider="openai", kind="batch").inc()
        texts = [it.get("text", "") or f"image {it.get('image').size if it.get('image') else ''}"
                 for it in items]
        return self._call(texts)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_embedder(settings: Settings | None = None) -> Embedder:
    """Return the configured embedder implementation.

    The chosen provider is selected from ``settings.embedding_provider``:
    ``mock``, ``local_hf``, or ``openai``.
    """
    s = settings or get_settings()
    name = s.embedding_provider
    log.info("building_embedder", provider=name)

    if name == "mock":
        return MockEmbedder(dim=s.embeddings_dim)
    if name == "local_hf":
        return LocalHFEmbedder(
            model_id=s.embedding_model_id,
            device=s.model_device,
            torch_dtype=s.model_torch_dtype,
        )
    if name == "openai":
        return OpenAIEmbedder(
            api_key=s.openai_api_key,
            model=s.openai_embedding_model,
            timeout=s.embedding_timeout_sec,
        )
    raise ProviderNotAvailableError(f"unknown embedding provider: {name}")


__all__ = [
    "Embedder",
    "MockEmbedder",
    "LocalHFEmbedder",
    "OpenAIEmbedder",
    "build_embedder",
]


# Keep `base64` import (used by tests that round-trip data URLs)
_ = base64
