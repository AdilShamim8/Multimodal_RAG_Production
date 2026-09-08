# Resume Bullets — Agentic RAG Platform

> 3–5 resume bullets derived from measured evidence. **Replace placeholders with real numbers from your eval runs.**

## Bullet 1 (architecture)

Designed and implemented a production-grade Agentic RAG platform combining hybrid retrieval (dense + lexical with Reciprocal Rank Fusion), cross-encoder reranking (BGE-reranker-v2-m3), agentic orchestration with a custom state machine, persistent memory with conflict resolution, RBAC enforced at the SQL layer, citation verification via LLM-judge, and reproducible evaluation with CI quality gates.

## Bullet 2 (retrieval quality)

Improved Recall@5 from `[dense baseline]` to `[hybrid+rerank]` (a `[X]%` improvement) by implementing hybrid retrieval with RRF fusion and cross-encoder reranking, measured against a `[N]`-item golden dataset across `[10]` query categories.

## Bullet 3 (security)

Defended against `[10]` known prompt injection attack patterns via layered defenses (input classifier, retrieved-content isolation, output sanitizer, tool argument validation), with zero unauthorized data leaks in `[N]` adversarial test cases.

## Bullet 4 (cost / latency)

Achieved p95 query latency of `[X]ms` at `$[Y]` per query by combining local BGE-m3 embeddings, local cross-encoder reranking, and GPT-4o-mini for generation with citation validation.

## Bullet 5 (evaluation + CI)

Built a reproducible evaluation framework with `[6]` baselines, `[4]` retrieval metrics (Recall@K, Precision@K, MRR, nDCG), `[6]` generation metrics (faithfulness, citation correctness, hallucination rate, etc.), and CI quality gates that block merges when faithfulness drops below `0.85`.

## Bullet 6 (production)

Deployed via Docker Compose / Kubernetes with blue/green deployment, nightly `pg_dump` backups to S3 with 30-day retention, OpenTelemetry tracing to Langfuse, and Prometheus metrics for system health.

---

## How to use these

- Pick the 3 that best match the job you're applying for.
- Replace `[bracketed]` placeholders with real numbers from your evaluation runs.
- **Never** claim a metric you didn't measure.
- If you only ran the smoke eval (10 items), say so: "on a 10-item smoke eval set".
- For interviews, be ready to defend every number — see `interview-guide.md`.
