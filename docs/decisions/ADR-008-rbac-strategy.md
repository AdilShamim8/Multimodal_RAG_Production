# ADR-008: RBAC enforced at SQL layer (pre-retrieval filtering)

- **Status**: Accepted
- **Date**: 2025-01-01

## Context

The system retrieves chunks based on user queries. Many chunks have access restrictions (role-based, project-based, or user-specific). Unauthorized chunks must NEVER appear in retrieval results, citations, or agent reasoning.

## Problem

Where to enforce authorization: in the retrieval SQL (pre-retrieval) or in application code (post-retrieval).

## Options considered

### Option A: Retrieve-then-filter (post-retrieval)

- Pros: simpler SQL; works with any vector DB.
- Cons: unauthorized chunks may appear in traces, logs, or LLM context before being filtered; pagination is broken (you might retrieve 10, filter out 8, and return 2 to the user); metadata leakage.

### Option B: Pre-retrieval filtering in SQL WHERE clause

- Pros: unauthorized chunks never enter the candidate set; no metadata leakage; correct pagination.
- Cons: requires a SQL function (`access_matches`); couples retrieval to RBAC.

### Option C: Per-user vector indexes

- Pros: maximum isolation.
- Cons: impractical at scale (one index per user/role combination).

## Decision

**Option B: Pre-retrieval filtering in SQL WHERE clause via the `rag.access_matches()` function.**

## Rationale

- Security: unauthorized chunks never enter the candidate set.
- Correctness: pagination works; the LLM never sees unauthorized content in its context.
- Auditability: a single SQL function is the chokepoint; we can test it exhaustively.

## Trade-offs

- The `access_matches()` function is a SQL function — debugging requires psql access.
- A poorly-tuned function could slow retrieval (we mark it IMMUTABLE and SECURITY DEFINER for performance).

## Consequences

- Every retrieval SQL query (dense, lexical, hybrid) includes `WHERE rag.access_matches(d.access_policy, :user_role, :user_projects, :user_id)`.
- Memory retrieval always includes `WHERE user_id = :user_id` (no `access_matches` needed — direct column filter).
- We have integration tests asserting:
  - Employee cannot retrieve manager-only chunks.
  - User A cannot retrieve User B's memories.
  - Role escalation via request body is blocked (role comes from JWT).

## What happens if this component fails?

- If `access_matches()` is dropped from the DB, retrieval queries fail loudly (function not found). No silent fall-through to "allow all".
- If the function returns true for everything (bug), our security tests catch it.

## How would we replace it later?

- Could move to row-level security (RLS) policies, but `access_matches` is more flexible (supports complex JSON access policies).
- Could move to a different DB by reimplementing the function in the new DB's SQL dialect.
