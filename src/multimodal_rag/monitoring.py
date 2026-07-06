"""Prometheus metrics for the API + pipeline.

Exposed at ``/metrics``. Counters/histograms are module-level singletons so
they are shared across all requests.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Info

INFO = Info(
    "multimodal_rag",
    "Build/runtime info for the multimodal-rag service.",
)

REQUESTS = Counter(
    "multimodal_rag_requests_total",
    "Total HTTP requests handled.",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "multimodal_rag_request_latency_seconds",
    "HTTP request latency in seconds.",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

PIPELINE_STAGE_LATENCY = Histogram(
    "multimodal_rag_pipeline_stage_seconds",
    "Latency of each RAG pipeline stage.",
    ["stage"],  # embed | retrieve | rerank | generate
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

EMBEDDING_OPS = Counter(
    "multimodal_rag_embedding_ops_total",
    "Embedding operations performed.",
    ["provider", "kind"],  # kind: text | image | batch
)

RETRIEVAL_RESULTS = Histogram(
    "multimodal_rag_retrieval_results",
    "Number of results returned by retrieval.",
    buckets=(1, 3, 5, 10, 20, 50, 100, 200),
)

RERANK_OPS = Counter(
    "multimodal_rag_rerank_ops_total",
    "Reranking operations performed.",
    ["provider"],
)

GENERATION_OPS = Counter(
    "multimodal_rag_generation_ops_total",
    "Generation operations performed.",
    ["provider"],
)

ERRORS = Counter(
    "multimodal_rag_errors_total",
    "Total errors by category.",
    ["category"],
)


def record_build_info(version: str, env: str) -> None:
    INFO.info({"version": version, "env": env})
