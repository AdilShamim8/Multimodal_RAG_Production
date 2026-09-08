# Adversarial Report

> Results of running the system against the adversarial query set (Phase 13).
> **Replace placeholders with real measurements.**

## Test set

`evals/datasets/adversarial.jsonl` — 15+ adversarial queries across categories:
- Irrelevant
- Ambiguous
- Conflicting sources
- Stale documents
- Prompt injection (direct)
- Indirect injection (via retrieved content)
- Unauthorized query
- Malformed file
- Tool failure (simulated)
- Model failure (malformed JSON)
- Agent loop (simulated)
- Hallucination bait (future date)
- Citation mismatch
- DoS via large query
- DoS via deep nesting

## Results

| ID  | Category              | Outcome  | Root cause              | Fix                          | Regression test                |
| --- | --------------------- | -------- | ----------------------- | ---------------------------- | ------------------------------ |
| A-1 | Direct injection      | PASS     | Input classifier + regex | n/a                          | `tests/security/test_prompt_injection.py` |
| A-2 | Indirect injection    | PASS     | Retrieved-content isolation | n/a                          | (covered by output sanitizer tests) |
| A-3 | Stale documents       | PASS     | Freshness boost penalizes expired | n/a                  | `tests/integration/test_freshness.py` |
| A-4 | Agent loop            | PASS     | Loop detection via args_hash | n/a                       | `tests/unit/test_agent_state.py` |
| A-5 | Unauthorized query    | PASS     | RBAC in SQL WHERE clause | n/a                          | `tests/security/test_rbac.py` |
| A-6 | Cross-user memory     | PASS     | `user_id` filter in memory retrieval | n/a             | `tests/security/test_rbac.py` |
| A-7 | Hallucination bait    | PASS     | Evidence sufficiency check + citation validation | n/a | (covered by integration tests) |
| A-8 | Citation mismatch     | PASS     | Citation validator drops unverified | n/a                  | `tests/unit/test_citation_builder.py` |

(Add rows as you discover and fix issues during Phase 13.)

## Issues found and fixed

(To be filled in as you run Phase 13.)

## Residual risks

- LLM compliance with content isolation (see `docs/security/prompt-injection.md`).
- LLM-judge bias (see `docs/learning/rag-evaluation.md`).
- Rate limit not yet implemented (see threat model).

## Sign-off

- Tested by: [your name]
- Date: YYYY-MM-DD
- Status: **APPROVED** / **BLOCKED** (delete one)
