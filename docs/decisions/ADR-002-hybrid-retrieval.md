# ADR-002: Hybrid retrieval (dense + lexical with RRF)

- **Status**: Accepted
- **Date**: 2025-01-01

## Context

We need to retrieve relevant document chunks given a user query. Dense (vector) retrieval handles semantic similarity well but misses exact matches. Lexical (BM25 / FTS) retrieval handles exact matches (names, IDs, codes) but misses synonyms.

## Problem

Choose between dense-only, lexical-only, or hybrid retrieval.

## Options considered

### Option A: Dense only

- Pros: simple, one index, handles semantic similarity.
- Cons: misses exact matches; course code "CS-101" might not retrieve the chunk that contains it.

### Option B: Lexical only

- Pros: exact matches, fast, well-understood.
- Cons: misses semantic similarity ("work-life balance" won't find "wellness program").

### Option C: Hybrid (dense + lexical, fused with RRF)

- Pros: best of both; well-established in IR literature.
- Cons: two indexes; need a fusion strategy; slightly higher latency.

### Option D: Hybrid with weighted score fusion

- Pros: more control over weights.
- Cons: dense cosine scores (0..1) and lexical BM25 scores (0..∞) are on incomparable scales; normalizing them is fragile.

## Decision

**Option C: Hybrid with Reciprocal Rank Fusion (RRF, k=60).**

## Rationale

- RRF uses only ranks, not scores, sidestepping the scale-comparability problem.
- RRF is the standard hybrid fusion method in IR; well-supported in production systems.
- Empirical results in `evals/reports/retrieval_comparison.md` show hybrid beats both dense-only and lexical-only on Recall@K and nDCG.

## Trade-offs

- Two indexes (ivfflat + GIN) consume more storage.
- Slightly higher p95 latency than dense-only.

## Consequences

- `retrieve()` runs both `dense_retrieve` and `lexical_retrieve` and fuses with `rrf_fuse()`.
- The fusion constant `k=60` is the value from the original RRF paper.

## What happens if this component fails?

- If lexical search fails (e.g., FTS index corrupt), fall back to dense-only.
- If dense search fails (e.g., embedder down), fall back to lexical-only.

## How would we replace it later?

- Switch fusion strategy by replacing `rrf_fuse()` with weighted-score fusion or a learned ranker.
- Add a third retriever (e.g., a sparse learned model like SPLADE) by extending the fusion.
