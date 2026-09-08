# Hybrid Retrieval

## Concept

Hybrid retrieval combines two retrieval strategies:
1. **Dense (vector) retrieval** — embed query and chunks into the same vector space; rank by cosine similarity. Handles semantic similarity ("work-life balance" ≈ "wellness program").
2. **Lexical (keyword) retrieval** — exact term matching (BM25 / Postgres FTS). Handles exact matches ("CS-101", "POL-2024-007").

Neither is sufficient alone:
- Dense misses exact matches: a query for "CS-101" might not retrieve the chunk that literally contains "CS-101" if the embeddings don't put them close together.
- Lexical misses synonyms: "work-life balance" won't match a chunk about "wellness program."

Hybrid retrieval runs both, then fuses the results.

## Why it exists

Real-world queries contain both semantic intent AND exact identifiers. A user asking "What is course CS-101?" wants semantic understanding (they're asking about a course) AND exact matching (CS-101 is a code, not a concept). Hybrid retrieval delivers both.

## How it works (in this project)

```
Query
  ↓
[Parallel]
  ├→ Dense retrieval (pgvector cosine)
  │    Returns: [chunk-A, chunk-B, chunk-C, ...] ranked by cosine
  │
  └→ Lexical retrieval (Postgres FTS ts_rank_cd)
       Returns: [chunk-B, chunk-D, chunk-A, ...] ranked by BM25-like score
  ↓
Reciprocal Rank Fusion (RRF)
  ↓
Top N fused candidates
```

### Reciprocal Rank Fusion (RRF)

RRF is a score-free way to merge two ranked lists:

```
score(chunk) = Σ over both lists of 1 / (k + rank_in_list)
```

where `k=60` (from the original RRF paper).

RRF is preferred over weighted-score fusion because dense cosine scores (0..1) and lexical BM25/FTS scores (0..∞) are on incomparable scales. RRF uses only ranks, sidestepping the problem.

## Where it appears in the code

- Dense: `src/retrieval/dense.py`
- Lexical: `src/retrieval/lexical.py`
- Fusion: `src/retrieval/hybrid.py` (`rrf_fuse()`)
- Engine: `src/retrieval/engine.py` (`retrieve()` with `strategy="hybrid"`)

## Trade-offs

### Hybrid vs. dense-only

- Hybrid: better Recall@K (catches both semantic and exact matches), but ~30ms extra latency for the lexical query.
- Dense-only: faster, but misses exact matches.

### Hybrid vs. lexical-only

- Hybrid: better Recall@K, but adds vector index storage.
- Lexical-only: faster, simpler, but misses semantic matches.

### RRF vs. weighted score fusion

- RRF: rank-only, no scale issues, simple, well-validated.
- Weighted: requires normalizing incomparable scores; fragile.

## Failure modes

- **One retriever is much worse than the other** → RRF averages out the worse one's contribution, but the worse one still adds noise. Mitigation: drop the worse retriever if Recall@K of hybrid < Recall@K of the better retriever alone.
- **Both retrievers miss the same chunk** → hybrid cannot help. Mitigation: reranking, query rewriting.

## Experiment results

See `evals/reports/retrieval_comparison.md`. **Replace placeholders with real measurements.**

Typical pattern (illustrative):

| Strategy          | Recall@5 | Recall@10 | MRR    | nDCG@10 | p95 latency (ms) |
| ----------------- | --------:| ---------:| ------:| -------:| ----------------:|
| Dense only        |     0.62 |      0.74 |  0.58  |   0.61  |             140  |
| Lexical only      |     0.48 |      0.61 |  0.45  |   0.49  |              35  |
| Hybrid (RRF)      |     0.78 |      0.88 |  0.74  |   0.78  |             170  |

## Further reading

- Cormack et al., "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods" (2009) — the original RRF paper.
- Manning et al., "Introduction to Information Retrieval" — IR fundamentals.
