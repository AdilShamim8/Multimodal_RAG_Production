# Vector Search

## Concept

Vector search finds the K nearest neighbors to a query vector in a vector space. In RAG, we search the `document_chunks.embedding` column for chunks closest to the query embedding.

## Why it exists

Semantic search requires comparing a query vector against all chunk vectors and returning the closest. A naive linear scan is O(N) — fine for 1000 chunks, infeasible for 10M.

Approximate Nearest Neighbor (ANN) indexes trade a small accuracy loss for a huge speedup. pgvector supports two ANN indexes:
- **ivfflat** — clusters vectors into lists; searches only the closest lists. Fast, simple.
- **hnsw** — graph-based; better recall at scale; more memory.

## How it works (in this project)

```sql
SELECT id, content, 1 - (embedding <=> :query_vec) AS score
FROM document_chunks
WHERE rag.access_matches(...)  -- RBAC filter BEFORE the search
ORDER BY embedding <=> :query_vec
LIMIT 10;
```

The `<=>` operator is cosine distance. We use ivfflat with `lists=100` (tune to ~sqrt(N)).

## Where it appears in the code

- Dense retrieval: `src/retrieval/dense.py`
- Migration: `alembic/versions/0001_init_schema.py` (creates the ivfflat index)

## Trade-offs

### ivfflat vs. HNSW

- ivfflat: simpler, less memory, requires `lists` tuning, slightly lower recall.
- HNSW: better recall, no tuning, more memory, slower inserts.

For our scale (<1M chunks), ivfflat is sufficient. For >1M, switch to HNSW.

### Pre-filter vs. post-filter

- Pre-filter (our approach): apply RBAC in WHERE clause before the vector search. Correct, secure.
- Post-filter: retrieve top-K, then filter. Broken pagination, metadata leakage.

We chose pre-filter. See ADR-008.

## Failure modes

- **Wrong embedding dimension** — `vector(1024)` column won't accept a 768-dim vector. Pick the embedder first, set the column type, never change.
- **Missing index** — full table scan, extremely slow. Always create the ivfflat/hnsw index.
- **Wrong distance metric** — pgvector supports cosine (`<=>`), L2 (`<->`), inner product (`<#>`). Pick one and use it consistently.

## Further reading

- pgvector README — https://github.com/pgvector/pgvector
- Johnson et al., "Billion-scale similarity search with GPUs" (FAISS paper)
- Malkov & Yashunin, "Efficient and robust approximate nearest neighbor search using HNSW" (2018)
