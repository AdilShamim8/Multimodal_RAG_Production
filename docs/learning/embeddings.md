# Embeddings

## Concept

An embedding is a vector representation of text that captures semantic meaning. Similar texts have similar embeddings (high cosine similarity). Embeddings enable semantic search: "work-life balance" and "wellness program" will have similar embeddings even though they share no words.

## Why it exists

Traditional keyword search (BM25, FTS) only matches exact terms. It cannot understand that "remote work policy" is about the same topic as "telecommuting guidelines." Embeddings bridge this gap by placing semantically similar texts close together in vector space.

## How it works

1. Choose an embedding model (we use `BAAI/bge-m3`, dim=1024).
2. Embed every chunk during ingestion → store as `vector(1024)` in `document_chunks.embedding`.
3. At query time, embed the query → vector.
4. Find chunks with highest cosine similarity to the query vector.

Cosine similarity: `1 - (a · b) / (|a| × |b|)`. In pgvector: `embedding <=> query_vector` (returns cosine distance; subtract from 1 for similarity).

## Where it appears in the code

- Embedder abstraction: `src/retrieval/embedders.py` (Protocol + BGE + OpenAI implementations)
- Dense retrieval: `src/retrieval/dense.py`
- During ingestion: `src/ingestion/indexer.py`

## Trade-offs

### Local (BGE-m3) vs. API (OpenAI text-embedding-3-large)

- Local: free, self-hosted, multilingual, 1024-dim (smaller = faster retrieval)
- API: $0.00013/1k tokens, 3072-dim, requires internet

We chose local for cost and control.

### Bi-encoder vs. cross-encoder

- Bi-encoder (embeddings): embed query and chunk separately; compare via cosine. Fast, scalable.
- Cross-encoder: see (query, chunk) jointly. More accurate, much slower. Used for reranking.

## Failure modes

- **Out-of-domain text** — embeddings trained on web text may not generalize to specialized vocabulary.
- **Short text** — single-word embeddings are noisy.
- **Multilingual mismatch** — embedding model must support the query language.

## Further reading

- BAAI, "BGE-m3" model card
- OpenAI, "New Embedding Models" blog post
- Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering" (2020)
