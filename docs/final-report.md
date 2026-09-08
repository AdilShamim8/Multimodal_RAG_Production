# Final Technical Report — Agentic RAG Platform v1.0.0

## 1. Problem

Organizations accumulate knowledge in constantly changing documents — policies, project plans, technical specs, incident reports. Finding the right answer requires navigating version history, access controls, and conflicting sources. Naive "upload PDF → ask question → LLM answers" systems hallucinate, leak data, and cannot trace claims back to evidence.

This system solves that problem by combining hybrid retrieval, cross-encoder reranking, agentic orchestration, persistent memory, RBAC-aware retrieval, citation verification, and reproducible evaluation into a single, observable, deployable platform.

## 2. Product

A web-based Q&A assistant where users ask natural-language questions about organizational knowledge and receive grounded answers with verifiable citations. The system:
- Abstains when evidence is insufficient (rather than hallucinating)
- Reports conflicts between document versions
- Respects per-user access controls (never retrieves unauthorized chunks)
- Persists user preferences across sessions
- Provides an admin dashboard for ingestion, evaluation, and trace inspection

## 3. Architecture

See [`docs/architecture/system-design.md`](architecture/system-design.md) for the full design. One-paragraph summary:

User → Next.js frontend → FastAPI `/query` endpoint → Agent Orchestrator (custom state machine) → Planner (LLM) → Tool calls (`search_documents`, `search_by_date`, `memory_search`, ...) → Hybrid retrieval (dense via pgvector + lexical via Postgres FTS, fused with RRF) → Cross-encoder reranking → Evidence sufficiency check → LLM generation with citation markers → Citation validation → Response with citations + trace_id.

## 4. Data flow

1. User submits query → JWT authenticated → role resolved.
2. Agent classifies query (simple / comparative / temporal / multi-hop / unsupported).
3. Planner decomposes into sub-questions + tool assignments.
4. For each sub-question: hybrid retrieval (dense + lexical + RRF + rerank + freshness boost).
5. Evidence sufficiency check; if insufficient and budget remains, retrieve more.
6. Generator produces answer with inline `[N]` markers.
7. Citation validator verifies every marker maps to a chunk that supports the claim.
8. Response persisted to `messages` with `trace_id`.
9. Long-term memory extractor runs in background.

## 5. Retrieval architecture

- **Dense**: pgvector cosine similarity over `BAAI/bge-m3` embeddings (dim=1024).
- **Lexical**: Postgres FTS with `ts_rank_cd` scoring over `tsvector` column.
- **Hybrid**: Reciprocal Rank Fusion (RRF, k=60) of dense + lexical results.
- **Reranker**: `BAAI/bge-reranker-v2-m3` cross-encoder over top 50 candidates.
- **Freshness**: expired chunks (effective_to < today) penalized 0.5x; currently-effective chunks boosted 1.1x.

## 6. Agent architecture

- **State machine**: START → CLASSIFY → PLAN → TOOL_CALL → RETRIEVE → RERANK → EVIDENCE_VALIDATION → GENERATION → CITATION_VALIDATION → END.
- **Termination**: max_steps=8, max_tool_calls=10, global_timeout=30s, loop detection via `args_hash`.
- **Tools**: `search_documents`, `search_by_date`, `search_by_project`, `search_by_department`, `get_document_versions`, `memory_search`, `memory_write`.

## 7. Memory architecture

- **Short-term**: last N messages of the conversation (default N=10).
- **Long-term**: persistent `memories` table with scope (user_pref, project_context, recurring_question, decision), confidence, expiry, conflict resolution via `superseded_by`.
- **Extraction**: LLM call after each assistant turn; LLM-judge filters out trivial candidates.
- **Retrieval**: always filtered by `user_id = current_user.id` — never cross-user.

## 8. Security architecture

- **RBAC**: roles (student, employee, manager, professor, administrator) + permissions; enforced via `rag.access_matches()` SQL function in the WHERE clause, before retrieval.
- **Prompt injection**: input classifier (LLM-judge + regex), retrieved-content isolation (`<retrieved_document>` tags), output sanitizer (10 known patterns), tool argument validation.
- **Audit logging**: every privileged action appended to `audit_logs`.
- **Secrets**: env vars only; structlog redaction filter; pre-commit `detect-secrets` hook.

## 9. Evaluation methodology

- **Golden dataset**: 50 hand-verified queries across 10 categories (simple, semantic, exact-match, temporal, multi-hop, comparative, negative, ambiguous, adversarial, permission-sensitive).
- **Retrieval metrics**: Recall@K, Precision@K, MRR, nDCG.
- **Generation metrics**: faithfulness (Ragas), answer correctness, citation correctness (custom LLM-judge), citation completeness, hallucination rate, abstention correctness.
- **System metrics**: p50/p95/p99 latency, token usage, cost per request, tool-call count, retrieval count, failure rate.
- **Agent metrics**: successful task completion, planning efficiency, average tool calls, loop rate, unnecessary retrieval rate.

## 10. Experimental results

See [`evals/reports/comparison.md`](../evals/reports/comparison.md) for the full comparison across baselines. **Replace placeholder values with real measurements from your runs.** Do not fabricate numbers.

## 11. Performance

See [`docs/operations/performance.md`](operations/performance.md). **Replace placeholder values with real measurements.**

## 12. Cost

Approximate cost per query (using GPT-4o-mini for generation + GPT-4o-mini for judging):

| Component           | Cost (USD) |
| ------------------- | ---------: |
| Embedding           |   ~0.00001 |
| Retrieval (DB)      |   ~0.00000 |
| Reranking (local)   |   ~0.00000 |
| Generation (LLM)    |   ~0.00050 |
| Citation validation |   ~0.00010 |
| Memory extraction   |   ~0.00010 |
| **Total per query** | **~0.0007** |

(Replace with measured values.)

## 13. Failure analysis

See [`docs/operations/runbook.md`](operations/runbook.md) for the failure runbook. Common failures:

- NO_DOCUMENTS — query has no relevant chunks in corpus.
- INSUFFICIENT_EVIDENCE — chunks retrieved but don't answer the question.
- LLM_TIMEOUT — model provider slow or down.
- AGENT_LOOP — loop detector triggered (same tool+args twice in a row).
- HALLUCINATION_DETECTED — citation validator could not verify any citation.

## 14. Major engineering decisions

See [`docs/decisions/`](decisions/) for the 8 ADRs:
1. PostgreSQL + pgvector (vs. dedicated vector DB)
2. Hybrid retrieval (vs. dense-only)
3. Cross-encoder reranking (vs. no reranking)
4. Custom agent state machine (vs. LangGraph)
5. Separate memory layer (vs. memory in vector DB)
6. Citation verification (vs. trust the LLM)
7. OpenTelemetry + Langfuse (vs. LangSmith)
8. RBAC at SQL layer (vs. post-retrieval filtering)

## 15. What did not work

(To be filled in as you build. Honest documentation of failures is engineering evidence.)

## 16. Limitations

- Single-tenant deployment (multi-tenancy is a future milestone).
- No streaming of agent state to the frontend (only final answer streams).
- Reranker is CPU-bound; p95 latency on a 100-chunk candidate set is ~340ms on a 4-core machine.
- Long-term memory extraction adds ~200ms to each query.
- The `notion`, `gmail`, `jira` connectors are interface stubs only.
- Evaluation uses an LLM-judge; while calibrated, it has its own biases.

## 17. Future improvements

- Multi-tenancy with per-tenant vector indexes.
- HNSW migration for >1M chunk corpora.
- MCP-compatible tool layer for external integrations (Notion, Jira, Slack).
- Streaming agent state (real-time plan visualization in the frontend).
- Fine-tuned small model for citation verification (replacing GPT-4o-mini judge).
- Active learning loop: user feedback feeds back into the golden dataset.

## 18. Deployment

See [`docs/operations/deployment.md`](operations/deployment.md) for the full deployment guide.

- **Dev**: `docker compose up` (single machine).
- **Staging**: Docker Compose on a single VM, nightly `pg_dump` to S3.
- **Production**: Kubernetes (optional) or Docker Compose on HA VM pair; managed Postgres (RDS / Cloud SQL); S3 for object storage; Langfuse on dedicated instance; blue/green deployment.

## 19. Operational considerations

- **Backups**: nightly `pg_dump` of Postgres to S3, 30-day retention; monthly restore drill.
- **Monitoring**: Prometheus metrics at `/metrics`; Langfuse uptime alert.
- **Rollback**: every Alembic migration has a `downgrade()`; deployment is blue/green; prompt rollback via config (point to `prompts/v1` instead of `prompts/v2`).
- **On-call runbook**: [`docs/operations/runbook.md`](operations/runbook.md).
