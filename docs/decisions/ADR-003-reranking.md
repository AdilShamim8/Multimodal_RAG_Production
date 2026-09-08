# ADR-003: Cross-encoder reranking with BGE-reranker-v2-m3

- **Status**: Accepted
- **Date**: 2025-01-01

## Context

After hybrid retrieval, the top-K candidates may still contain irrelevant chunks. A reranker can re-score (query, chunk) pairs jointly using a cross-encoder model.

## Problem

Choose between no reranker, a small/fast reranker, or a large cross-encoder.

## Options considered

### Option A: No reranker

- Pros: lowest latency.
- Cons: lower precision@K; more noise in the LLM context.

### Option B: Small reranker (e.g., MiniLM)

- Pros: fast (CPU-friendly).
- Cons: weaker accuracy.

### Option C: BGE-reranker-v2-m3 (cross-encoder)

- Pros: state-of-the-art on MTEB reranking; multilingual.
- Cons: ~340ms p95 on CPU for 50 candidate pairs.

### Option D: Cohere / Voyage reranker API

- Pros: managed, no GPU needed.
- Cons: per-call cost; external dependency; rate limits.

## Decision

**Option C: BGE-reranker-v2-m3, self-hosted.**

## Rationale

- Best accuracy among self-hostable options.
- No per-call cost.
- Multilingual (matches BGE-m3 embedder).
- CPU is acceptable for our scale; we can GPU-accelerate in prod if needed.

## Trade-offs

- p95 latency jumps from ~170ms (hybrid) to ~340ms (hybrid+rerank).
- CPU-bound — needs careful batching on shared infrastructure.

## Consequences

- Reranker runs as a singleton in the API process.
- Candidate count is capped at 50 (configurable) to bound reranker cost.
- `reranker_top_k=5` is the default (configurable).

## What happens if this component fails?

- If the reranker model fails to load, retrieval falls back to hybrid (no rerank) with a warning log.

## How would we replace it later?

- Swap `BGECrossEncoderReranker` for a different reranker class implementing the `Reranker` protocol.
- Or move to an API-based reranker (Cohere) by adding a new `Reranker` implementation.
