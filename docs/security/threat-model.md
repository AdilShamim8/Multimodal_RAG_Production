# Threat Model — Agentic RAG Platform

> STRIDE per asset. Each threat has mitigations and residual risk.

## Assets

1. **Retrieved chunks** — document content; access-controlled.
2. **User memory** — personal preferences, project context; per-user.
3. **LLM prompts** — system behavior; should not be revealed.
4. **Tool calls** — agent actions; arguments must be schema-valid.
5. **API endpoints** — public-facing; subject to auth and rate limits.
6. **Database** — all data; subject to SQL injection and credential leak.
7. **Audit logs** — append-only; must not be tampered with.
8. **Traces** — contain metadata; must not leak PII or secrets.

## STRIDE analysis

### Spoofing

| Threat                                  | Mitigation                                      | Residual risk |
| --------------------------------------- | ----------------------------------------------- | ------------- |
| Attacker spoofs a user identity         | JWT signed with `JWT_SECRET`; short-lived (60m) | None if JWT_SECRET is kept secret |
| Attacker spoofs the API                 | TLS termination at load balancer                | None if TLS is enforced |
| Attacker spoofs the LLM provider        | HTTPS to provider; certificate validation       | None |

### Tampering

| Threat                                  | Mitigation                                      | Residual risk |
| --------------------------------------- | ----------------------------------------------- | ------------- |
| Attacker tampers with chunks            | DB access restricted; SQLAlchemy parameterized queries | DB credentials leak |
| Attacker tampers with audit logs        | Append-only; admin-only access; nightly backup  | Insider threat |
| Attacker tampers with prompts           | Prompts versioned in git; CI runs detect-secrets | None |
| Attacker tampers with tool args         | JSON-schema validation in `execute_tool()`      | Schema bugs |

### Repudiation

| Threat                                  | Mitigation                                      | Residual risk |
| --------------------------------------- | ----------------------------------------------- | ------------- |
| User denies a query                     | All queries logged with `trace_id` + `user_id`  | None |
| Admin denies an action                  | All privileged actions logged in `audit_logs`   | None |

### Information disclosure

| Threat                                  | Mitigation                                      | Residual risk |
| --------------------------------------- | ----------------------------------------------- | ------------- |
| Unauthorized user retrieves chunks      | RBAC in SQL WHERE clause (`access_matches()`)   | Function bug — mitigated by tests |
| Cross-user memory leakage               | `user_id` filter in memory retrieval            | None |
| Prompt leakage                          | System prompt not exposed to user; output sanitizer blocks "reveal system prompt" | LLM compliance |
| Secret leakage in logs                  | Structlog redaction filter; pre-commit detect-secrets | Filter incomplete |
| PII leakage in traces                   | PII redaction; `query_hash` instead of raw query in span attributes | Redaction incomplete |

### Denial of service

| Threat                                  | Mitigation                                      | Residual risk |
| --------------------------------------- | ----------------------------------------------- | ------------- |
| Agent loops                             | Loop detection (`args_hash`), max_steps, global timeout | None |
| Large query DoS                         | Pydantic validators cap query at 5000 chars     | None |
| Many concurrent queries                 | Per-user rate limit (TODO); DB pool caps        | Rate limit not yet implemented |
| Malformed file ingestion                | File type validation; size cap                  | None |
| Retrieval poisoning (large candidate count) | `candidate_count` capped at 100 in config   | Config change |

### Elevation of privilege

| Threat                                  | Mitigation                                      | Residual risk |
| --------------------------------------- | ----------------------------------------------- | ------------- |
| User submits `role:admin` in request body | Role read from JWT, not request body           | None |
| User injects tool args to bypass filter | JSON-schema validation; per-tool permission check | Schema bugs |
| Indirect prompt injection via retrieved content | Retrieved-content isolation (`<retrieved_document>` tags); output sanitizer | LLM compliance |

## Attack surfaces

1. **`/query` endpoint** — accepts user query; runs through full agent pipeline.
2. **`/documents/ingest`** — accepts file upload; admin only.
3. **`/memory`** — accepts memory edits; per-user.
4. **`/admin/*`** — admin only; protected by `require_permission("admin")`.
5. **Retrieved chunks** — content from documents; could contain indirect prompt injection.

## Mitigations by layer

### Network layer
- TLS everywhere (load balancer terminates).
- CORS restricted to known origins.

### Application layer
- JWT auth on all endpoints except `/health` and `/auth/login`.
- Per-route permission checks via `require_permission()`.
- Pydantic request validation.

### Data layer
- RBAC in SQL WHERE clause (`access_matches()`).
- Memory retrieval filtered by `user_id`.
- Audit log append-only.

### LLM layer
- Input classifier (regex + LLM-judge).
- Retrieved-content isolation.
- Output sanitizer (10 known patterns).
- Tool argument JSON-schema validation.
- Citation validation (LLM-judge).

### Observability layer
- PII redaction in logs.
- Secret scanning in CI.
- Trace attributes use `query_hash`, not raw query.

## Residual risks

1. **LLM compliance with isolation** — the LLM is instructed to treat `<retrieved_document>` as data, but a sufficiently sophisticated injection could still influence it. Mitigation: output sanitizer catches known patterns.
2. **LLM-judge bias** — citation correctness depends on the LLM-judge, which has its own biases. Mitigation: calibrate against 20 hand-labeled items.
3. **Insider threat** — an admin with DB access could tamper with audit logs. Mitigation: ship audit logs to a separate, append-only store (S3 with object lock) in production.
4. **Rate limit not implemented** — the system is vulnerable to query DoS. TODO: add per-user rate limit in FastAPI middleware.
