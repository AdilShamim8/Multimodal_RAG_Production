# ADR-005: Separate memory layer (not in vector DB)

- **Status**: Accepted
- **Date**: 2025-01-01

## Context

The agent needs short-term (conversation) and long-term (persistent user preferences, project context) memory. Long-term memory must be: inspectable, editable, deletable, auditable, and always filtered by `user_id` to prevent cross-user leakage.

## Problem

Where to store long-term memory: in the same `document_chunks` table as documents, in a separate `memories` table, or in a dedicated memory store.

## Options considered

### Option A: Memories in `document_chunks`

- Pros: one retrieval path.
- Cons: pollutes the document corpus; access policy is different (per-user, not per-role); cannot easily enforce `user_id` filter; "memory vs document" mixing causes confusion in citations.

### Option B: Separate `memories` table with its own retrieval

- Pros: clean separation; `user_id` filter is trivial; different lifecycle (expiry, conflict resolution); memories never leak into document citations.
- Cons: two retrieval paths to maintain.

### Option C: External memory service (e.g., Mem0)

- Pros: managed.
- Cons: external dependency; harder to audit; per-call cost.

## Decision

**Option B: Separate `memories` table with its own retrieval.**

## Rationale

- Cross-user leakage is a critical security risk; a dedicated table makes the `user_id` filter unavoidable.
- Memories have different lifecycle (expiry, conflict resolution) from documents.
- Citations from documents vs memories are visibly different to the user.

## Trade-offs

- Two retrieval code paths (document retrieval + memory retrieval).

## Consequences

- `src/memory/` is a separate module with its own retrieval.
- Memory retrieval always filters on `user_id = current_user.id`.
- Memory extraction is an LLM call after each turn; LLM-judge filters out trivial memories.
- Memories have `expires_at` and `superseded_by` for lifecycle management.

## What happens if this component fails?

- If memory extraction fails, the user's request still succeeds (extraction is non-blocking).
- If memory retrieval fails, the agent proceeds without memories.

## How would we replace it later?

- Could swap to an external memory service by replacing `src/memory/long_term.py` with a client implementation.
