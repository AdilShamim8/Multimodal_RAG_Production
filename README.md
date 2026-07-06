# Multimodal RAG Production

The original repository is a single 71-cell Jupyter notebook that demonstrates a
multimodal RAG pipeline for recipe retrieval: text or image queries are embedded
with NVIDIA Nemotron Embed VL, retrieved via cosine similarity over 10 096
recipe image+text pairs, optionally reranked with NVIDIA Llama-Nemotron Rerank VL,
and finally summarised by Qwen3-VL-2B-Instruct.

This rebuild turns that notebook into a **modular, tested, deployable**
Python package with:

- **Pluggable providers** — `mock`, `local_hf` (Nemotron + Qwen3-VL), or `openai` for
  embeddings, reranking, and generation, all behind clean protocols.
- **Pluggable vector stores** — `chroma` (embedded), `qdrant` (self-hosted),
  `faiss` (in-memory), all behind one interface.
- **FastAPI REST API** — `/health`, `/ingest`, `/retrieve`, `/rerank`,
  `/generate`, `/rag/query`, plus `/metrics` for Prometheus.
- **Typer CLI** — `serve`, `ingest`, `query`, `download-models`, `reset`, `info`.
- **Production polish** — structured logging (structlog), retry (tenacity),
  rate limiting (slowapi), in-memory cache (cachetools), Prometheus metrics,
  comprehensive exception hierarchy, Dockerfile + docker-compose, GitHub Actions CI.
- **Tests** — pytest unit tests for every module + API integration tests.
- **CPU-friendly defaults** — `mock` providers run anywhere; flip a single env
  var to switch to real models.

---

## Quickstart

```bash
# 1. Install (CPU-only, mock providers — works on any laptop)
make install

# 2. Configure
cp .env.example .env

# 3. Ingest the bundled 200-recipe sample
make ingest

# 4. Start the API
make serve
# → http://localhost:8000/docs

# 5. Or query from the CLI
multimodal-rag query --text "tomato basil pasta" --top-k 3
```

## Switching to real models

Edit `.env`:

```bash
EMBEDDING_PROVIDER=local_hf
EMBEDDING_MODEL_ID=nvidia/Nemotron-Embed-VL
RERANKER_PROVIDER=local_hf
RERANKER_MODEL_ID=nvidia/Llama-Nemotron-Rerank-VL
GENERATOR_PROVIDER=local_hf
GENERATOR_MODEL_ID=Qwen/Qwen3-VL-2B-Instruct
```

Install the GPU extras (requires `torch`):

```bash
pip install -e ".[gpu]"
multimodal-rag download-models
```

## Docker

```bash
# Just the API
docker build -t multimodal-rag .
docker run -p 8000:8000 --env-file .env multimodal-rag

# Full stack: API + Qdrant + Redis + Prometheus + Grafana
docker compose up -d
```

## Architecture at a glance

```
                ┌──────────┐
   query ──────►│ Embedder │──► vector ─┐
   (text/image) └──────────┘            │
                                         ▼
                                ┌────────────────┐
                                │  Vector Store  │ (Chroma/Qdrant/FAISS)
                                └────────────────┘
                                         │
                                  top-K candidates
                                         ▼
                                ┌────────────────┐
                                │   Reranker     │ (optional)
                                └────────────────┘
                                         │
                                  reranked candidates
                                         ▼
                                ┌────────────────┐
                                │   Generator    │ ──► summary
                                └────────────────┘
```

See `docs/architecture.md` for the full system diagram and `docs/api.md` for
The REST contract.

## Project layout

```
multimodal-rag-production/
├── src/multimodal_rag/         # the package
│   ├── app.py                  # FastAPI factory
│   ├── cli.py                  # Typer CLI
│   ├── config.py               # pydantic-settings
│   ├── schemas.py              # shared Pydantic models
│   ├── models/                 # embedder, reranker, generator (+mock/local_hf/openai)
│   ├── stores/                 # VectorStore protocol + Chroma/Qdrant/FAISS
│   ├── data/                   # dataset loader + bundled 200-recipe sample
│   ├── pipeline/               # RAG orchestrator
│   └── api/                    # FastAPI routes + middleware + deps
├── tests/                      # pytest unit + API integration tests
├── scripts/                    # build_sample_dataset.py, prometheus.yml
├── docs/                       # architecture, api, deployment, troubleshooting
├── notebooks/                  # original notebook preserved
├── Dockerfile + docker-compose.yml
├── .github/workflows/ci.yml    # lint + test + docker build smoke test
├── pyproject.toml + Makefile
└── .env.example
```

## Tech stack

| Layer         | Library                                |
|---------------|----------------------------------------|
| Web framework | FastAPI + Uvicorn                      |
| Config        | pydantic-settings                      |
| HTTP client   | httpx + tenacity (retry)               |
| Rate limit    | slowapi                                |
| Cache         | cachetools (LRU)                       |
| Vector DB     | Qdrant, ChromaDB, FAISS                |
| ML (optional) | torch + transformers (Nemotron, Qwen3-VL) |
| CLI           | Typer + Rich                           |
| Logging       | structlog                              |
| Monitoring    | prometheus-client                      |
| Testing       | pytest + pytest-asyncio + pytest-cov   |
| Lint/format   | ruff + mypy                            |

## License

MIT — see [LICENSE](LICENSE).
