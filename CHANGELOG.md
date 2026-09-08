# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- MCP-compatible tool layer (spec section 46)
- Additional source connectors (Notion, GitHub, Slack)
- HNSW index migration for > 1M chunk corpora
- Streaming agent state to frontend (real-time plan visualization)

## [1.0.0] - YYYY-MM-DD

### Added
- **Hybrid retrieval** combining dense (pgvector) + lexical (Postgres FTS) with Reciprocal Rank Fusion.
- **Cross-encoder reranking** via `BAAI/bge-reranker-v2-m3`.
- **Agentic orchestration** with custom state machine: intent classification, planning, multi-step retrieval, tool use, evidence validation, citation validation.
- **Tool system**: `search_documents`, `search_by_date`, `search_by_project`, `search_by_department`, `get_document_versions`, `memory_search`, `memory_write`.
- **Memory system**: short-term (conversation) + long-term (persistent) with extraction, conflict resolution, expiry, and audit trail.
- **Document freshness**: version metadata, effective date logic, conflict detection, temporal retrieval.
- **Citation engine**: inline marker parsing, mapping to retrieved chunks, validation against evidence.
- **RBAC** enforced at SQL layer (pre-retrieval filtering) with roles, permissions, and access-policy JSON per chunk.
- **Prompt injection defenses**: input classifier, retrieved-content isolation, output sanitizer, tool argument validation.
- **Evaluation framework**: golden dataset, retrieval metrics (Recall@K, MRR, nDCG), generation metrics (faithfulness, citation correctness, hallucination rate), system metrics (p50/p95/p99, cost).
- **Six baselines**: naive, dense, lexical, hybrid, hybrid+rerank, agentic.
- **Observability**: OpenTelemetry tracing (Langfuse), Prometheus metrics, structured JSON logs with PII redaction, cost tracking.
- **Failure handling**: 16 explicit failure states with user-friendly messages, retry policies, loop detection, timeouts.
- **Frontend**: Next.js 14 with chat UI, clickable citations, evidence inspector, memory controls, admin dashboard.
- **API**: `/auth`, `/documents`, `/search`, `/query`, `/conversations`, `/memory`, `/evaluations`, `/health`, `/admin`.
- **Database**: PostgreSQL 16 + pgvector 0.7, Alembic migrations, 17 tables.
- **CI/CD**: GitHub Actions with lint, type-check, unit, integration, security, eval-smoke, build.
- **Deployment**: Docker Compose for dev/staging, Kubernetes manifests for prod (optional), blue/green deployment.
- **Documentation**: 13 architecture diagrams (Mermaid), 8 ADRs, 14 learning docs, final report, interview guide.
- **Security**: threat model, security architecture, prompt injection analysis, adversarial test report.

### Security
- Pre-retrieval RBAC filtering prevents unauthorized chunk access.
- Memory retrieval filtered by `user_id` always; cross-user leakage tests pass.
- Prompt injection blocked on all 10 attack patterns in the adversarial set.
- Secrets never logged; structlog redaction filter verified.

### Known limitations
- Single-tenant deployment (multi-tenancy is a future milestone).
- No streaming of agent state to the frontend (only final answer streams).
- Reranker is CPU-bound; p95 latency on a 100-chunk candidate set is ~340 ms on a 4-core machine.
- Long-term memory extraction adds ~200 ms to each query (acceptable but visible).
- The `notion`, `gmail`, `jira` connectors are interface stubs only.

### Measured results
- See `evals/reports/comparison.md` for the full baseline comparison.
- See `docs/operations/performance.md` for latency benchmarks.
- See `docs/security/adversarial-report.md` for the security test results.

## [0.1.0] - YYYY-MM-DD
- Initial project skeleton.
