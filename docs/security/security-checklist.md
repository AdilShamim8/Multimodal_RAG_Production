# Security Checklist

> Pre-release security review. Mark each as PASS / FAIL / N/A.

## Authentication

- [PASS] JWT auth on all endpoints except `/health` and `/auth/login`
- [PASS] JWT_SECRET is 64+ chars, stored in env var
- [PASS] Access tokens expire in 60 minutes
- [PASS] Refresh tokens expire in 7 days
- [PASS] Token type validated on every request
- [PASS] Role read from JWT, never from request body

## Authorization (RBAC)

- [PASS] Roles defined: student, employee, manager, professor, administrator
- [PASS] Permissions defined: read:document, write:document, ingest, eval, admin
- [PASS] `access_matches()` SQL function enforces RBAC in WHERE clause
- [PASS] Memory retrieval filters by `user_id = current_user.id` always
- [PASS] Admin endpoints protected by `require_permission("admin")`
- [PASS] Ingest endpoint protected by `require_permission("ingest")`
- [PASS] Eval endpoints protected by `require_permission("eval")`

## Prompt injection defense

- [PASS] Input classifier with 10 known patterns
- [PASS] Retrieved-content isolation via `<retrieved_document>` tags
- [PASS] Output sanitizer scans generated answers
- [PASS] Tool argument JSON-schema validation
- [PASS] Tests cover all 10 attack patterns (`tests/security/test_prompt_injection.py`)

## Secrets

- [PASS] No secrets in code (searched with `detect-secrets`)
- [PASS] No secrets in git history (searched with `trufflehog` if available)
- [PASS] `.env` is gitignored
- [PASS] `.env.example` has safe placeholders
- [PASS] Structlog redaction filter masks known secret patterns
- [PASS] Pre-commit hook runs `detect-secrets`

## Network

- [PASS] CORS restricted to known origins
- [PASS] TLS termination at load balancer (in production)
- [TODO] Per-user rate limit (not yet implemented — see threat model residual risk)

## Database

- [PASS] SQLAlchemy parameterized queries throughout (no SQL injection)
- [PASS] DB credentials in env vars
- [PASS] `access_matches()` marked IMMUTABLE SECURITY DEFINER
- [PASS] Audit log is append-only

## Observability

- [PASS] PII redaction in logs (emails, SSNs, credit cards)
- [PASS] `query_hash` used in span attributes instead of raw query
- [PASS] API keys never logged

## Audit

- [PASS] All privileged actions logged to `audit_logs`
- [PASS] Audit log entries include actor, action, target, metadata, trace_id
- [PASS] Audit log backed up nightly

## Testing

- [PASS] `tests/security/test_rbac.py` — 4 RBAC boundary tests
- [PASS] `tests/security/test_prompt_injection.py` — 10 injection patterns
- [PASS] CI runs all security tests on every PR

## Documentation

- [PASS] `docs/security/threat-model.md` — STRIDE per asset
- [PASS] `docs/security/security-architecture.md` — defense in depth
- [PASS] `docs/security/prompt-injection.md` — attack patterns + mitigations
- [PASS] `docs/security/adversarial-report.md` — adversarial test results (Phase 13)

## Residual risks (accepted)

- LLM compliance with content isolation — see `docs/security/prompt-injection.md`
- LLM-judge bias — calibrated against 20 hand-labeled items
- Rate limit not yet implemented — documented as TODO
- Insider threat (admin with DB access) — mitigated by shipping audit logs to S3 in production

## Sign-off

- Reviewed by: [your name]
- Date: YYYY-MM-DD
- Status: **APPROVED** / **BLOCKED** (delete one)
