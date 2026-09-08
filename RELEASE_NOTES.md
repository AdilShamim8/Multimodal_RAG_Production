# Release Notes — v1.0.0

> Production-grade Agentic RAG Platform — first public release.

## Highlights

This release delivers a complete, evaluated, secured, observable, and deployable Agentic RAG system. Every capability in the spec is implemented, tested, and documented.

## What's inside

### Retrieval
- Hybrid retrieval (dense via pgvector + lexical via Postgres FTS) fused with Reciprocal Rank Fusion (RRF).
- Cross-encoder reranking with `BAAI/bge-reranker-v2-m3`.
- Configurable top_k, candidate count, similarity threshold, fusion strategy, reranking threshold, metadata filters.
- Document freshness boost based on effective dates.

### Agentic
- Custom state machine orchestrator (no LangGraph dependency).
- Intent classification, planning, query decomposition, multi-step retrieval.
- Tool registry with JSON-schema-validated arguments, per-tool permissions, timeouts.
- Loop detection via `args_hash`, max-steps, global timeout, evidence-sufficiency check.

### Memory
- Short-term: last N messages of the conversation.
- Long-term: persistent memories with scope, confidence, expiry, conflict resolution.
- Memory retrieval is hybrid and always filtered by `user_id`.

### Citations
- Inline `[N]` markers in generated answers.
- Marker-to-chunk mapping validated post-generation.
- Citation correctness metric enforced in CI.

### Security
- RBAC enforced in retrieval SQL (pre-filtering, not post-filtering).
- Prompt injection defenses: input classifier, retrieved-content isolation, output sanitizer, tool argument validation.
- Audit logging on every privileged action.
- PII redaction in logs.

### Evaluation
- Golden dataset with 10 categories (simple, semantic, exact-match, temporal, multi-hop, comparative, negative, ambiguous, adversarial, permission-sensitive).
- Retrieval metrics: Recall@K, Precision@K, MRR, nDCG.
- Generation metrics: faithfulness, answer correctness, citation correctness, citation completeness, hallucination rate, abstention correctness.
- Six baselines compared in `evals/reports/comparison.md`.
- CI quality gate: faithfulness ≥ 0.85, hallucination rate ≤ 0.10.

### Observability
- OpenTelemetry tracing exported to Langfuse.
- Prometheus metrics for system health.
- Structured JSON logs with `trace_id` and `user_id`.
- Cost tracking per request.

### Frontend
- Next.js 14 chat UI with streaming responses.
- Clickable citations that scroll to and highlight evidence.
- Evidence inspector modal.
- Memory controls (list, edit, delete, export).
- Admin dashboard (ingest, eval report, traces).

### Deployment
- Docker Compose for dev/staging.
- Kubernetes manifests for prod (optional).
- Blue/green deployment with rollback.
- Nightly `pg_dump` backups to S3.

## How to upgrade

This is the first release. No upgrade path needed.

## Known issues

- See "Known limitations" in [CHANGELOG.md](CHANGELOG.md).
- File bugs at `https://github.com/your-org/agentic-rag-platform/issues`.

## Credits

Built following the Principal AI Engineer build prompt. Engineering journal in [`docs/engineering-journal.md`](docs/engineering-journal.md).
