# Multimodal RAG Production — Architecture

This document describes the system architecture, data flow, and design
decisions of the rebuild.

## High-level architecture

```
              ┌──────────────────────────┐
              │  Client (CLI / curl /    │
              │  any HTTP client)        │
              └────────────┬─────────────┘
                           │ HTTP (JSON)
                           ▼
              ┌──────────────────────────┐
              │  FastAPI (uvicorn)       │
              │  ─ /health, /metrics     │
              │  ─ /ingest               │
              │  ─ /retrieve             │
              │  ─ /rerank               │
              │  ─ /generate             │
              │  ─ /rag/query            │
              └────────────┬─────────────┘
                           │
              ┌────────────▼─────────────┐
              │  RAGPipeline             │
              │  (orchestrator)          │
              └────────────┬─────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  ┌──────────┐      ┌────────────┐     ┌────────────┐
  │ Embedder │ ───► │ VectorStore│ ───►│  Reranker  │
  │  (mock / │      │ (Chroma /  │     │  (mock /   │
  │ local_hf │      │  Qdrant /  │     │  local_hf /│
  │ / openai)│      │  FAISS)    │     │  openai)   │
  └──────────┘      └────────────┘     └────────────┘
                                              │
                                              ▼
                                       ┌────────────┐
                                       │  Generator │
                                       │  (mock /   │
                                       │ local_hf / │
                                       │ openai)    │
                                       └────────────┘
```

## Module responsibilities

| Module                | Responsibility                                         |
|-----------------------|--------------------------------------------------------|
| `config.py`           | Centralised pydantic-settings; reads `.env`           |
| `schemas.py`          | Pydantic models shared across API/CLI/pipeline         |
| `models/embedder.py`  | Embedder protocol + `mock` / `local_hf` / `openai`     |
| `models/reranker.py`  | Reranker protocol + 3 implementations                  |
| `models/generator.py` | Generator protocol + 3 implementations                 |
| `stores/`             | VectorStore protocol + Chroma/Qdrant/FAISS             |
| `data/dataset.py`     | Load 200-sample / HF 10k / local JSON                  |
| `pipeline/rag.py`     | Wire embed → retrieve → rerank → generate              |
| `api/routes/`         | FastAPI route handlers                                 |
| `api/middleware.py`   | Metrics, structured logging, exception handlers        |
| `api/deps.py`         | Dependency injection for FastAPI                       |
| `cli.py`              | Typer CLI (`serve`, `ingest`, `query`, …)              |
| `logging.py`          | structlog configuration                                |
| `monitoring.py`       | Prometheus counters / histograms                       |
| `cache.py`            | In-memory LRU cache decorator                          |
| `rate_limit.py`       | SlowAPI limiter                                        |

## Data flow (RAG query)

1. Client POSTs `/rag/query` with `query_text` and/or `query_image`.
2. `RAGPipeline.run()` is called.
3. **Retrieve** stage: the query is embedded and searched against the vector
   store. Returns the top-K candidates.
4. **Rerank** stage (optional): each candidate is re-scored by the reranker.
5. **Generate** stage (optional): the top-N candidates are passed as context
   to the generator, which produces a natural-language summary.
6. The response includes the retrieved items, reranked items (if any), the
   summary, and per-stage timings.

## Provider selection

Providers are selected via environment variables:

| Setting                  | Allowed values             |
|--------------------------|----------------------------|
| `EMBEDDING_PROVIDER`     | `mock` / `local_hf` / `openai` |
| `RERANKER_PROVIDER`      | `mock` / `local_hf` / `openai` |
| `GENERATOR_PROVIDER`     | `mock` / `local_hf` / `openai` |
| `VECTOR_STORE`           | `chroma` / `qdrant` / `faiss` |

The `mock` providers run anywhere (CPU, no network) and are used by default
and in CI. The `local_hf` providers load the original NVIDIA Nemotron + Qwen3-VL
weights via `transformers`. The `openai` providers call the OpenAI API.

## Why pluggable providers?

The original notebook is monolithic: it bakes the model choice into the
top-level cells. In production, you want to:

- Run unit tests without downloading 16 GB of weights.
- A/B test embedders without rewriting the pipeline.
- Swap to OpenAI when a GPU is unavailable, then back to local when one frees up.

The protocol + factory pattern lets all three of those happen with a single
env var change.
