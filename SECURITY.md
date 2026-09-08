# Security

> Security is a first-class product feature of this system. This document is the entry point; deeper material lives in [`docs/security/`](docs/security/).

## Threat model summary

STRIDE per asset. Full model in [`docs/security/threat-model.md`](docs/security/threat-model.md).

| Asset                  | Primary threats                                            | Defenses                                              |
| ---------------------- | ---------------------------------------------------------- | ----------------------------------------------------- |
| Retrieved chunks       | Unauthorized access, cross-user leakage                   | RBAC enforced in SQL `WHERE`; per-user memory filter  |
| LLM prompts            | Prompt injection, indirect injection via documents        | Input classifier + output sanitizer + retrieved-content isolation |
| Tool calls             | Argument injection, privilege escalation                   | JSON-schema validation; per-tool permission check     |
| User memory            | Cross-user leakage, memory pollution                      | `user_id` filter always; LLM-judge extraction filter  |
| API endpoints          | Auth bypass, rate-limit DoS                                | JWT validation; per-route rate limit; CSRF protection |
| Database               | SQL injection, credential leak                            | SQLAlchemy parameterized queries; secrets in env vars |
| Audit log              | Tampering, deletion                                        | Append-only; nightly backup; access restricted to admin |
| Traces                 | PII leak, secret leak                                      | PII redaction; secret scanning at log time           |

## Authorization (RBAC)

- Roles: `student, employee, manager, professor, administrator`.
- Permissions: `read:document, write:document, ingest, eval, admin`.
- `role_permissions` table drives the check.
- **The role is read from the JWT, never from the request body.**
- Retrieval SQL filters on `access_matches(access_policy, user_role, user_projects, user_id)` **before** the vector search.
- Memory retrieval filters on `user_id = current_user.id` always.

See [`docs/security/security-architecture.md`](docs/security/security-architecture.md) for the full design.

## Prompt injection defenses

1. **Input classifier** — a small LLM call flags inputs that contain instructions to override system behavior. Flagged inputs are routed to a safe refusal template.
2. **Retrieved-content isolation** — retrieved chunks are wrapped in `<retrieved_document>` XML tags; the system prompt explicitly says content inside these tags is data, never instructions.
3. **Output sanitizer** — scans the generated answer for known injection patterns (`ignore previous instructions`, `</system>`, `role: assistant`, `new instructions:`). If found, the response is blocked and logged.
4. **Tool argument validation** — every tool call's arguments are validated against the tool's JSON schema before execution.

See [`docs/security/prompt-injection.md`](docs/security/prompt-injection.md) for attack patterns and mitigations.

## Secrets management

- All secrets in environment variables; never in code, never in git.
- `.env.example` has safe placeholders; `.env` is gitignored.
- Structlog has a redaction filter that masks known secret key patterns.
- API keys are never logged in traces (filtered at the exporter).
- A pre-commit hook runs `detect-secrets` to prevent accidental commits.

## Audit logging

Every privileged action writes to `audit_logs`:

| Action                | When                                    |
| --------------------- | --------------------------------------- |
| `ingest`              | Document uploaded                       |
| `delete_document`     | Document soft-deleted                   |
| `role_change`         | User's role changed                     |
| `memory_edit`         | Long-term memory edited by user         |
| `memory_delete`       | Long-term memory deleted by user        |
| `admin_query`         | Admin ran a privileged query            |
| `eval_run`            | Evaluation experiment executed          |
| `config_change`       | Production config changed               |

Audit logs are append-only, backed up nightly, and accessible only to `administrator` role.

## Vulnerability disclosure

Found a security issue? Email `security@your-org.example` (replace with your real address). Do not open a public GitHub issue. We respond within 72 hours.

## Security checklist

See [`docs/security/security-checklist.md`](docs/security/security-checklist.md) for the full pre-release checklist.

## Adversarial test results

See [`docs/security/adversarial-report.md`](docs/security/adversarial-report.md) for the results of running the system against the adversarial query set.
