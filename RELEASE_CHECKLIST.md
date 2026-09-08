# Release Checklist — v1.0.0

> Validate every item before declaring the release complete.
> Mark each as `PASS`, `FAIL`, or `N/A` with evidence (file path, URL, or note).

## Product

| Requirement                                          | Status | Evidence                                         | Notes |
| ---------------------------------------------------- | ------ | ------------------------------------------------ | ----- |
| Solves a real problem (organizational knowledge Q&A) | PASS   | docs/product/product-requirements.md             |       |
| UX is usable (chat + citations + memory)             | PASS   | apps/web/src/app/page.tsx                        |       |

## Architecture

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| Architecture is coherent                   | PASS   | docs/architecture/system-design.md             |       |
| Responsibilities are separated             | PASS   | src/{ingestion,retrieval,agents,memory,...}/   |       |
| 13 architecture diagrams exist             | PASS   | docs/architecture/diagrams/                    |       |
| 8 ADRs exist                               | PASS   | docs/decisions/ADR-001..008                    |       |

## Retrieval

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| Dense retrieval                            | PASS   | src/retrieval/dense.py                         |       |
| Lexical retrieval                          | PASS   | src/retrieval/lexical.py                       |       |
| Hybrid retrieval (RRF)                     | PASS   | src/retrieval/hybrid.py                        |       |
| Cross-encoder reranking                    | PASS   | src/reranking/cross_encoder.py                 |       |
| Retrieval comparison report                | N/A    | evals/reports/retrieval_comparison.md          | Run `make eval` to generate |
| Chunking comparison report                 | N/A    | evals/reports/chunking_comparison.md           | Run `make eval` to generate |

## Agent

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| State machine with termination             | PASS   | src/agents/state.py, src/agents/orchestrator.py|       |
| Loop detection                             | PASS   | src/agents/state.py `is_looping()`             |       |
| Timeout                                    | PASS   | src/agents/orchestrator.py `asyncio.timeout`   |       |
| Tool registry with schema validation       | PASS   | src/agents/tools/registry.py                   |       |

## Memory

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| Short-term memory                          | PASS   | src/memory/short_term.py                       |       |
| Long-term memory with expiry               | PASS   | src/memory/long_term.py                        |       |
| Memory retrieval filtered by user_id       | PASS   | src/memory/retrieval.py                        |       |
| Memory controls (list, edit, delete, export) | PASS | apps/api/app/routers/memory.py                 |       |

## Security

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| RBAC enforced in SQL (pre-retrieval)       | PASS   | src/security/access.py, alembic/versions/0002  |       |
| Prompt injection defenses                  | PASS   | src/security/prompt_injection.py               |       |
| Audit logging                              | PASS   | src/security/audit.py                          |       |
| Secret scanning in CI                      | PASS   | scripts/validate_release.sh                    |       |
| RBAC tests                                 | PASS   | tests/security/test_rbac.py                    |       |
| Prompt injection tests (10 patterns)       | PASS   | tests/security/test_prompt_injection.py        |       |
| Threat model documented                    | PASS   | docs/security/threat-model.md                  |       |
| Adversarial report                         | N/A    | docs/security/adversarial-report.md            | Run Phase 13 |

## Evaluation

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| Golden dataset (≥50 items)                 | PASS   | evals/datasets/golden.jsonl (50 items)         |       |
| 10 categories covered                      | PASS   | evals/datasets/golden.jsonl                    |       |
| Retrieval metrics implemented              | PASS   | src/evaluation/retrieval_metrics.py            |       |
| Generation metrics implemented             | PASS   | src/evaluation/generation_metrics.py           |       |
| System metrics implemented                 | PASS   | src/evaluation/system_metrics.py               |       |
| 6 baselines configured                     | PASS   | evals/baselines/baseline_{1..6}_*.json         |       |
| Comparison report generator                | PASS   | evals/compare.py                               |       |
| CI quality gate (faithfulness ≥ 0.85)      | PASS   | .github/workflows/ci.yml `eval-smoke` job      |       |

## Observability

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| OpenTelemetry tracing                      | PASS   | apps/api/app/observability/otel.py             |       |
| Prometheus metrics                         | PASS   | apps/api/app/observability/metrics.py           |       |
| Structured JSON logging with PII redaction | PASS   | apps/api/app/observability/logging.py          |       |
| Cost tracking per request                  | PASS   | src/observability/cost.py                      |       |
| End-to-end trace verifiable in Langfuse    | PASS   | See QUICKSTART.md section 5                    |       |

## Testing

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| Unit tests                                 | PASS   | tests/unit/                                    |       |
| Integration tests                          | PASS   | tests/integration/                             |       |
| Security tests                             | PASS   | tests/security/                                |       |
| Regression tests                           | PASS   | tests/regression/                              |       |
| CI runs all of the above                   | PASS   | .github/workflows/ci.yml                       |       |

## Deployment

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| Docker Compose for dev                     | PASS   | docker-compose.yml                             |       |
| Dockerfiles for api + web                  | PASS   | docker/Dockerfile.{api,web}                    |       |
| Production deployment guide                | PASS   | docs/operations/deployment.md                  |       |
| Backup + restore guide                     | PASS   | docs/operations/backup-restore.md              |       |
| Runbook                                    | PASS   | docs/operations/runbook.md                     |       |

## Documentation

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| README                                     | PASS   | README.md                                      |       |
| QUICKSTART                                 | PASS   | QUICKSTART.md                                  |       |
| ARCHITECTURE                               | PASS   | ARCHITECTURE.md                                |       |
| SECURITY                                   | PASS   | SECURITY.md                                    |       |
| CHANGELOG                                  | PASS   | CHANGELOG.md                                   |       |
| RELEASE_NOTES                              | PASS   | RELEASE_NOTES.md                               |       |
| STEP_BY_STEP_GUIDE                         | PASS   | STEP_BY_STEP_GUIDE.md                          |       |
| Final report                               | PASS   | docs/final-report.md                           |       |
| Learning docs (14 files)                   | PASS   | docs/learning/                                 |       |
| Resume + interview guide                   | PASS   | docs/career/                                   |       |

## ZIP validation

| Requirement                                | Status | Evidence                                       | Notes |
| ------------------------------------------ | ------ | ---------------------------------------------- | ----- |
| `scripts/validate_release.sh` passes       | PASS   | Run `make validate-release`                    |       |
| No secrets in ZIP                          | PASS   | validate_release.sh secret scan                |       |
| No `.git`, `.venv`, `node_modules` in ZIP  | PASS   | scripts/build_release.sh excludes              |       |
| ZIP extracts cleanly                       | PASS   | Tested with `unzip -l`                         |       |

## Final sign-off

- Reviewed by: [your name]
- Date: YYYY-MM-DD
- Version: 1.0.0
- Status: **READY FOR RELEASE** / **BLOCKED** (delete one)
