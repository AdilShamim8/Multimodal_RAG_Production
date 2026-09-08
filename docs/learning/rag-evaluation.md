# Evaluation

## Concept

RAG evaluation measures retrieval quality, generation quality, and system performance. Without evaluation, you cannot:
- Distinguish a real improvement from noise.
- Catch regressions before users do.
- Justify architectural decisions.

## Why it exists

A RAG system without evaluation is a demo, not a product. "It feels better" is not engineering evidence. We need reproducible numbers across baselines.

## How it works (in this project)

### Golden dataset

`evals/datasets/golden.jsonl` — 50 hand-verified queries across 10 categories:
- simple_factual
- semantic
- exact_match
- temporal
- multi_hop
- comparative
- negative_unsupported
- ambiguous
- adversarial
- permission_sensitive

Each item has: id, category, query, expected_answer_pattern, expected_chunks, expected_documents, expected_behavior, access_role, notes.

### Retrieval metrics

| Metric      | What it measures                              |
| ----------- | --------------------------------------------- |
| Recall@K    | Fraction of relevant items in top K retrieved |
| Precision@K | Fraction of top-K retrieved that are relevant |
| MRR         | Mean Reciprocal Rank — 1/rank of first relevant |
| nDCG@K      | Normalized Discounted Cumulative Gain — accounts for graded relevance |

See `src/evaluation/retrieval_metrics.py`.

### Generation metrics

| Metric                | What it measures                              |
| --------------------- | --------------------------------------------- |
| Faithfulness          | All claims supported by evidence (Ragas)      |
| Answer correctness    | Answer matches expected                       |
| Context relevance     | Retrieved context is relevant                 |
| Citation correctness  | Every [N] marker maps to a supporting chunk   |
| Citation completeness | Every supported claim has a citation          |
| Hallucination rate    | Fraction of unsupported claims                |
| Abstention correctness| For negative queries: did we abstain?         |

See `src/evaluation/generation_metrics.py`.

### System metrics

p50/p95/p99 latency, token usage, cost per request, tool-call count, retrieval count, failure rate.

### Baselines

6 baselines, each representing a step up in sophistication:
1. Naive (dense, no rerank, no agent)
2. Dense only
3. Lexical only
4. Hybrid (no rerank)
5. Hybrid + rerank
6. Full agentic

### CI quality gate

On every PR:
- Run `eval-smoke` (10-item subset, < 5 min).
- If faithfulness < 0.85 → fail the build.

Nightly:
- Run full eval.
- Upload report as artifact.

## Where it appears in the code

- Retrieval metrics: `src/evaluation/retrieval_metrics.py`
- Generation metrics: `src/evaluation/generation_metrics.py`
- System metrics: `src/evaluation/system_metrics.py`
- Eval runner: `evals/run.py`
- Comparison report: `evals/compare.py`
- CI workflow: `.github/workflows/ci.yml`, `.github/workflows/eval.yml`

## Trade-offs

### Ragas vs. custom metrics

- Ragas: well-known, handles faithfulness/context-relevance/answer-correctness.
- Custom: needed for citation correctness, abstention correctness, hallucination rate.

We use both. Ragas for what it's good at, custom for what it isn't.

### LLM-judge vs. human evaluation

- LLM-judge: fast, cheap, scales to 1000s of queries.
- Human: accurate, slow, expensive.

We use LLM-judge, calibrated against 20 hand-labeled examples. Cohen's kappa > 0.8 required before trusting the judge.

## Failure modes

- **Tiny golden dataset** — high variance. Mitigated by 50-item minimum.
- **LLM-judge bias** — false positives/negatives. Mitigated by calibration.
- **Quality gate not enforced** — eval runs but doesn't block merges. Mitigated by wiring into CI.

## Further reading

- Es et al., "RAGAS: Automated Evaluation of Retrieval Augmented Generation" (2023)
- Liu et al., "LLM-as-a-Judge: Evaluating LLMs with LLMs" (2023)
