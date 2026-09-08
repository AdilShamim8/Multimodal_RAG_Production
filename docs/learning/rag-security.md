# RAG Security

## Concept

RAG systems have unique security considerations beyond traditional web apps:

1. **Retrieved content is untrusted** — documents may contain malicious instructions.
2. **Retrieval must respect access controls** — not just the API layer.
3. **Memory is per-user** — never cross-contaminate.
4. **The LLM is a vector for prompt injection** — both from user input AND from retrieved content.
5. **Traces may leak PII** — queries, retrieved chunks, and LLM responses all contain user data.

## Why it exists

Enterprise RAG systems handle sensitive information: HR policies, financial reports, employee data. A breach — whether through unauthorized retrieval, prompt injection, or trace leakage — can be catastrophic. Security must be designed in from day one, not bolted on.

## How it works (in this project)

### RBAC at SQL layer

```sql
WHERE rag.access_matches(d.access_policy, :user_role, :user_projects, :user_id)
```

This function is called BEFORE the vector search. Unauthorized chunks never enter the candidate set. See `src/security/access.py` and ADR-008.

### Memory isolation

```python
stmt = select(Memory).where(
    Memory.user_id == user_id,  # ALWAYS
    ...
)
```

Memory retrieval always filters by `user_id`. Cross-user leakage is impossible by construction. See `src/memory/retrieval.py`.

### Prompt injection defense

Four layers (defense in depth):
1. Input classifier — `src/security/prompt_injection.py::classify_input()`
2. Retrieved-content isolation — `<retrieved_document>` tags
3. Output sanitizer — `src/security/prompt_injection.py::sanitize_output()`
4. Tool argument validation — `src/agents/tools/registry.py::_validate_args()`

See `docs/security/prompt-injection.md` for details.

### PII redaction

Structlog has a redaction filter that masks:
- OpenAI API keys (`sk-...`)
- Hugging Face tokens (`hf_...`)
- AWS access keys (`AKIA...`)
- GitHub tokens (`ghp_...`)
- Email addresses
- US SSNs
- 16-digit credit card numbers

See `apps/api/app/observability/logging.py`.

## Where it appears in the code

- RBAC: `src/security/rbac.py`, `src/security/access.py`, `alembic/versions/0002_access_matches_function.py`
- Prompt injection: `src/security/prompt_injection.py`
- Audit logging: `src/security/audit.py`
- Tests: `tests/security/`

## Trade-offs

### Pre-retrieval vs. post-retrieval filtering

- Pre-retrieval: secure, correct pagination, no metadata leakage. Requires SQL function.
- Post-retrieval: simpler SQL, but leaks metadata in traces and breaks pagination.

We chose pre-retrieval. See ADR-008.

### LLM-judge vs. deterministic checks

- LLM-judge: high accuracy, can detect nuanced injection, but adds latency and cost.
- Deterministic (regex): fast, free, but only catches known patterns.

We use both — regex first (fast), LLM-judge as backup (accurate).

## Failure modes

- **`access_matches()` bug** — could allow unauthorized access. Mitigated by 4 RBAC tests.
- **LLM ignores content isolation** — could follow instructions in retrieved content. Mitigated by output sanitizer.
- **LLM-judge has bias** — could false-positive or false-negative. Mitigated by calibration against hand-labeled examples.
- **PII redaction incomplete** — could leak emails or secrets in traces. Mitigated by structlog filter + secret scanning in CI.

## Further reading

- OWASP Top 10 for LLMs — https://owasp.org/www-project-top-10-for-large-language-model-applications/
- NIST AI Risk Management Framework
- Microsoft, "Mitigating Prompt Injection Attacks"
