# Lexical Search

## Concept

Lexical search matches exact terms between query and documents. We use Postgres FTS (Full-Text Search) with `tsvector` and `ts_rank_cd` scoring.

## Why it exists

Vector search handles semantic similarity but misses exact matches. A query for "CS-101" (a course code) needs lexical search — embeddings may not place "CS-101" close to its mention in a chunk.

## How it works (in this project)

1. At ingestion time, each chunk's `tsv` column is populated with `to_tsvector('english', content)`.
2. At query time, the query is converted to a tsquery: `plainto_tsquery('english', query)`.
3. Chunks matching the tsquery are scored with `ts_rank_cd(tsv, tsquery)`.
4. Top K returned.

```sql
SELECT id, content, ts_rank_cd(tsv, plainto_tsquery('english', :q)) AS score
FROM document_chunks
WHERE tsv @@ plainto_tsquery('english', :q)
  AND rag.access_matches(...)
ORDER BY score DESC
LIMIT 10;
```

## Where it appears in the code

- Lexical retrieval: `src/retrieval/lexical.py`
- tsv column: defined in `alembic/versions/0001_init_schema.py`
- GIN index on tsv: same migration

## Trade-offs

### BM25 vs. Postgres FTS

- BM25 (e.g., via OpenSearch): industry standard, well-tuned.
- Postgres FTS: built-in, no extra service, slightly less accurate.

We chose Postgres FTS to keep our stack simple (single datastore). If FTS quality becomes a bottleneck, we can add OpenSearch as a sidecar.

### Stemming

Postgres FTS applies stemming (e.g., "running" → "run"). This is good for English but may not be ideal for other languages. Configure the language: `to_tsvector('german', content)`.

## Failure modes

- **No FTS index** — full table scan, slow. Always create the GIN index.
- **Wrong language** — stemming won't work. Set the language per chunk if multilingual.
- **Stop words** — common words ("the", "and") are dropped. Usually fine but can cause surprising misses.

## Further reading

- PostgreSQL docs, "Full Text Search" — https://www.postgresql.org/docs/current/textsearch.html
- Manning et al., "Introduction to Information Retrieval" — BM25 chapter
