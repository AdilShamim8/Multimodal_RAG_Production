# Troubleshooting

## Common issues

### `ModuleNotFoundError: No module named 'multimodal_rag'`

The package wasn't installed in the active Python environment. Re-run:

```bash
pip install -e .
```

If you have multiple Python versions, prefix with `python3.13 -m pip install -e .`
or whichever interpreter you used.

### `ProviderNotAvailableError: local_hf embedder requires the 'gpu' extra`

You set `EMBEDDING_PROVIDER=local_hf` but didn't install torch + transformers:

```bash
pip install -e ".[gpu]"
```

### `VectorStoreConnectionError: cannot reach Qdrant at http://localhost:6333`

Qdrant isn't running. Start it:

```bash
docker compose up -d qdrant
# or
docker run -p 6333:6333 qdrant/qdrant
```

### Chroma: `ValueError: Expected metadata value to be a str, int, float, bool, …`

You're using an old version of `chromadb` that doesn't handle nested metadata.
Upgrade:

```bash
pip install -U chromadb
```

Our `ChromaStore` already flattens nested metadata, so this should not occur
in normal operation.

### `/metrics` returns 404

The Prometheus endpoint is registered at app startup. If you don't see it,
ensure `ENABLE_METRICS=true` (default) and that you're hitting `/metrics`
(not `/metrics/`).

### `RateLimitExceeded` on every request

The default is 60 req/min per IP. Raise `RATE_LIMIT_PER_MINUTE` or decorate
specific routes with `@limiter.limit("1000/minute")`.

### Generation is super slow

If `GENERATOR_PROVIDER=local_hf` and you're on CPU, expect 5–60 seconds per
response. Either:
- Switch to `mock` (instant, deterministic, no LLM)
- Switch to `openai` (fast, but requires API key)
- Add a GPU

### Qwen3-VL OOMs on first generate

Lower `GENERATE_MAX_NEW_TOKENS` to 256 and ensure you're on a GPU with
≥ 8 GB VRAM. The model itself is ~4 GB FP16.

### Embedding mismatch between query and stored vectors

Make sure the embedder you used at ingest time matches the one at query time.
The pipeline does not validate this for you. A common gotcha: ingest with
`EMBEDDING_PROVIDER=mock`, then switch to `local_hf` and query — the vector
dimensions and semantics will not match.

### How do I clear the vector store?

```bash
multimodal-rag reset
# or via API
curl -X DELETE http://localhost:8000/admin/cache/clear   # not implemented; use CLI
```

### Tests are slow

CI runs in ~10 s. Locally, if tests are slow, ensure:
- `CACHE_ENABLED=false` (set by `conftest.py`)
- `APP_LOG_LEVEL=WARNING` (set by `conftest.py`)
- You're not accidentally using Qdrant (which needs Docker)

## Getting help

- Check the structured logs at `APP_LOG_LEVEL=DEBUG`.
- Inspect `/metrics` for error counters.
- Open an issue on the original repo:
  https://github.com/AdilShamim8/Multimodal_RAG_Production/issues
