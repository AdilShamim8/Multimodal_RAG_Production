# Reranking

## Concept

Reranking is a second-pass retrieval step that uses a more expensive but more accurate model to re-score the top candidates from initial retrieval.

- **Initial retrieval (cheap)**: dense + lexical → top 50 candidates.
- **Reranking (expensive)**: cross-encoder → top 5 evidence chunks.

The cross-encoder sees (query, chunk) pairs jointly, allowing it to capture fine-grained relevance that bi-encoders (used in dense retrieval) miss.

## Why it exists

Bi-encoders (used for initial dense retrieval) embed query and chunk separately, then compare via cosine similarity. This is fast (embed once, compare many times) but loses fine-grained interaction between query and chunk.

Cross-encoders see the full (query, chunk) pair together, allowing attention between query tokens and chunk tokens. This is much more accurate but much slower — you can't pre-compute chunk embeddings.

The pattern: use the fast bi-encoder to get top 50 candidates, then use the slow cross-encoder to re-score those 50 and pick the top 5.

## How it works (in this project)

```python
# 1. Get 50 candidates from hybrid retrieval
candidates = await retrieve(query, strategy="hybrid", top_k=50)

# 2. Rerank with cross-encoder
reranker = BGECrossEncoderReranker(model_name="BAAI/bge-reranker-v2-m3")
top_5 = await reranker.rerank(query, candidates, top_k=5)
```

The reranker:
1. Forms 50 (query, chunk) pairs.
2. Runs each pair through the cross-encoder → relevance score (0..1 after normalization).
3. Sorts by score, returns top 5.

## Where it appears in the code

- Reranker base: `src/reranking/base.py` (`Reranker` protocol)
- BGE implementation: `src/reranking/cross_encoder.py` (`BGECrossEncoderReranker`)
- Wired into retrieval: `src/retrieval/engine.py` (strategy `"hybrid_reranked"`)

## Trade-offs

### Reranking vs. no reranking

- With reranking: higher precision@K (top 5 are more relevant), lower hallucination (LLM context is cleaner).
- Without reranking: ~170ms faster (on CPU), but more noise in the top 5.

### BGE-reranker-v2-m3 vs. Cohere Rerank API

- BGE (self-hosted): no per-call cost; CPU-bound (~340ms p95 for 50 candidates on 4 cores).
- Cohere (API): per-call cost; fast (no local compute); external dependency.

For our scale, BGE is the right choice.

## Failure modes

- **Reranker model fails to load** → fall back to hybrid (no rerank) with a warning log.
- **Reranker is too slow** → reduce `candidate_count` from 50 to 20, or move reranker to a separate worker.
- **Reranker disagrees with hybrid ranking** → trust the reranker (it's more accurate).

## Experiment results

See `evals/reports/retrieval_comparison.md`. **Replace placeholders with real measurements.**

Typical pattern (illustrative):

| Strategy          | Recall@5 | MRR    | nDCG@5 | p95 latency (ms) |
| ----------------- | --------:| ------:| ------:| ----------------:|
| Hybrid (no rerank)|     0.78 |  0.74  |   0.78 |             170  |
| Hybrid + rerank   |     0.84 |  0.81  |   0.85 |             340  |

## Further reading

- Nogueira & Cho, "Passage Re-ranking with BERT" (2019) — the original cross-encoder reranking paper.
- BAAI, "BGE-reranker-v2-m3" model card on Hugging Face.
