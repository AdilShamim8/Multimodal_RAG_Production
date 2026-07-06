# API reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI) and
`http://localhost:8000/redoc` (ReDoc).

## Authentication

If `API_KEY` is set, every request must include an `X-API-Key` header matching
that value. Otherwise authentication is disabled.

---

## `GET /health`

Liveness + readiness probe.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "providers": {
    "embedding": "mock",
    "reranker": "mock",
    "generator": "mock"
  },
  "vector_store": "chroma",
  "dataset_size": 200
}
```

## `GET /ready`

Kubernetes-style readiness probe. Returns `{"ready": true, "store": "chroma",
"count": 200}`.

## `POST /ingest`

Load a dataset into the vector store.

**Request body:**
```json
{
  "source": "sample",   // sample | hf | local
  "limit": 200,         // optional cap
  "force": false
}
```

**Response:**
```json
{
  "ingested": 200,
  "skipped": 0,
  "duration_sec": 0.42,
  "dataset_source": "sample"
}
```

## `POST /retrieve`

Embed the query and return the top-K candidates from the vector store.

**Request body:**
```json
{
  "query_text": "tomato basil pasta",
  "query_image": null,           // or a base64 data URL or http(s) URL
  "top_k": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "recipe": { "id": "recipe-0001", "title": "Tomato Basil Pasta", "text": "..." },
      "score": 0.81,
      "rank": 1
    }
  ],
  "query_kind": "text",
  "elapsed_sec": 0.012
}
```

## `POST /rerank`

Rerank a list of candidate recipes against a text query.

**Request body:**
```json
{
  "query_text": "tomato",
  "candidates": [ { "id": "r1", "title": "...", "text": "..." } ],
  "top_k": 5
}
```

## `POST /generate`

Generate a summary over the supplied recipes.

**Request body:**
```json
{
  "query": "tomato basil pasta",
  "recipes": [ { "id": "r1", "title": "...", "text": "..." } ],
  "style": "summary",      // summary | comparison | recipe_card
  "max_new_tokens": 512,
  "temperature": 0.7
}
```

## `POST /rag/query`

End-to-end RAG: retrieve → rerank → generate.

**Request body:**
```json
{
  "query_text": "tomato basil pasta",
  "query_image": null,
  "top_k": 5,
  "rerank": true,
  "rerank_top_k": 20,
  "generate": true,
  "generate_style": "summary",
  "max_new_tokens": 512,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "retrieved": [ { "recipe": {...}, "score": 0.81, "rank": 1 } ],
  "reranked": [ { "recipe": {...}, "score": 0.92, "rank": 1 } ],
  "summary": "Top pick: Tomato Basil Pasta. ...",
  "timings": { "retrieve": 0.012, "rerank": 0.034, "generate": 0.156, "total": 0.202 },
  "providers": { "embedding": "mock", "reranker": "mock", "generator": "mock", "vector_store": "chroma" }
}
```

## `GET /metrics`

Prometheus exposition format. Counts + histograms for HTTP requests, pipeline
stages, and provider ops.

## Error responses

All errors return a JSON envelope:
```json
{
  "error": {
    "error": "ValidationError",
    "detail": "at least one of query_text or query_image is required",
    "code": "400"
  }
}
```

| HTTP | Class                       | When                                  |
|------|-----------------------------|---------------------------------------|
| 400  | `ValidationError`           | Bad request payload                   |
| 401  | `AuthenticationError`       | Missing/invalid `X-API-Key`           |
| 422  | `DatasetError`              | Dataset cannot be loaded              |
| 429  | `RateLimitExceededError`    | Rate limit hit                        |
| 500  | `RetrievalError` / `PipelineError` | Internal pipeline failure     |
| 502  | `EmbeddingProviderError` etc. | Upstream provider failure            |
| 503  | `ProviderNotAvailableError` / `VectorStoreConnectionError` | Service unavailable |
