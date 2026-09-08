# Architecture

> One-page overview. Full diagrams and ADRs live in [`docs/architecture/`](docs/architecture/) and [`docs/decisions/`](docs/decisions/).

## High-level

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────────────────┐
│   Browser   │────▶│  Next.js    │────▶│  FastAPI (/query, /search, ...)  │
│  (User)     │     │  (web:3000) │     │  (api:8000)                      │
└─────────────┘     └─────────────┘     └────────────────┬─────────────────┘
                                                          │
                                                          ▼
                                          ┌──────────────────────────────┐
                                          │   Agent Orchestrator         │
                                          │   (custom state machine)     │
                                          └───────────┬──────────────────┘
                                                      │
              ┌───────────────────────────────────────┼───────────────────────────┐
              ▼                                       ▼                           ▼
   ┌────────────────────┐               ┌────────────────────────┐   ┌─────────────────────┐
   │  Planner / Class.  │               │  Tool Registry         │   │  Memory Layer       │
   │  (LLM)             │               │  (search_documents,    │   │  (short + long term)│
   └─────────┬──────────┘               │   search_by_date, ...) │   └──────────┬──────────┘
             │                          └───────────┬────────────┘              │
             │                                      │                           │
             └──────────────────┬───────────────────┘                           │
                                ▼                                               │
                ┌───────────────────────────────┐                               │
                │  Retrieval Engine             │                               │
                │  - dense (pgvector)           │◀──────────────────────────────┘
                │  - lexical (Postgres FTS)     │
                │  - hybrid (RRF)               │
                │  - freshness-aware            │
                └──────────────┬────────────────┘
                               │
                               ▼
                ┌───────────────────────────────┐
                │  Cross-encoder Reranker       │
                │  (BGE-reranker-v2-m3)         │
                └──────────────┬────────────────┘
                               │
                               ▼
                ┌───────────────────────────────┐
                │  Citation Builder + Validator │
                └──────────────┬────────────────┘
                               │
                               ▼
                ┌───────────────────────────────┐
                │  LLM Generation               │
                │  (gpt-4o-mini via provider)   │
                └──────────────┬────────────────┘
                               │
                               ▼
                       ┌──────────────┐
                       │  Response    │
                       │  + trace_id  │
                       └──────────────┘
```

## Data stores

- **PostgreSQL 16** — relational data, document chunks, embeddings (`pgvector`), full-text search (`tsvector`), audit logs, conversations, memories, evaluations.
- **Redis** — embedding cache, query cache (TTL 5 min).
- **S3-compatible storage** — original document files (PDF, etc.), backup dumps.
- **Langfuse (Postgres backend)** — OpenTelemetry traces.

## Request flow (one query)

1. User submits query via Next.js → FastAPI `/query`.
2. FastAPI authenticates the user (JWT) and resolves role + permissions.
3. Agent Orchestrator starts a state machine.
4. Classifier routes the query (simple / comparative / temporal / multi-hop / unsupported).
5. Planner generates sub-questions and assigns tools.
6. For each sub-question: hybrid retrieval (dense + lexical, fused with RRF), then cross-encoder rerank, then freshness boost.
7. Evidence sufficiency check — if insufficient and budget remains, retrieve more.
8. Generator produces answer with inline `[N]` citation markers.
9. Citation validator verifies every marker maps to a chunk that supports the claim.
10. Response is persisted to `messages` with `trace_id`. Long-term memory extractor runs in the background.

## Authorization model

- Roles: `student, employee, manager, professor, administrator`.
- Each chunk has an `access_policy` JSON: `{roles: [...], projects: [...], users: [...]}`.
- Retrieval SQL filters on `access_matches(access_policy, user_role, user_projects, user_id)` in the `WHERE` clause, **before** the vector search.
- Memory retrieval filters on `user_id = current_user.id` always.
- No post-retrieval filtering. No client-side role claims (role is from JWT).

## Observability

- Every request gets a `trace_id` (UUID).
- OpenTelemetry spans for every significant operation (retrieval, rerank, generate, validate, tool call).
- Spans exported to Langfuse via OTLP.
- Prometheus metrics for system health (latency, cost, failure rate).
- Structured JSON logs with `trace_id` and `user_id` on every line.
- PII redaction in the logger.

## Deployment

- **Dev**: `docker compose up` (single machine).
- **Staging**: Docker Compose on a single VM, with nightly `pg_dump` to S3.
- **Production**: Kubernetes (optional) or Docker Compose on a HA VM pair. Cloud-managed Postgres (RDS / Cloud SQL). S3 for object storage. Langfuse on a dedicated instance. Blue/green deployment.

See [`docs/operations/deployment.md`](docs/operations/deployment.md) for the full guide.

## Failure handling

Every failure has an explicit enum value and a user-friendly message. See [`src/core/failures.py`](src/core/failures.py) and [`docs/operations/runbook.md`](docs/operations/runbook.md).

| Failure                | User-facing message                                                |
| ---------------------- | ------------------------------------------------------------------ |
| NO_DOCUMENTS           | "I couldn't find any documents matching your question."            |
| INSUFFICIENT_EVIDENCE  | "I don't have enough evidence to answer this confidently."         |
| LLM_TIMEOUT            | "The model is taking too long. Please try again."                  |
| AGENT_LOOP             | "I'm having trouble reasoning through this. Could you rephrase?"   |
| HALLUCINATION_DETECTED | "I generated an answer I cannot verify. Withholding response."     |
