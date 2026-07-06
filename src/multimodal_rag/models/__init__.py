"""Model provider subpackage.

Each provider family (embedder / reranker / generator) exposes:
* a Protocol describing the contract,
* a factory ``build_*`` function that returns the configured implementation,
* concrete implementations for ``mock``, ``local_hf``, and ``openai``.

The factories are the only public entry points — routes and pipeline stages
should never import concrete classes directly.
"""

from multimodal_rag.models.embedder import Embedder, build_embedder
from multimodal_rag.models.generator import Generator, build_generator
from multimodal_rag.models.reranker import Reranker, build_reranker

__all__ = [
    "Embedder",
    "Reranker",
    "Generator",
    "build_embedder",
    "build_reranker",
    "build_generator",
]
