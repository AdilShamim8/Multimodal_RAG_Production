# Memory

## Concept

Memory in RAG refers to information that persists across queries. Two layers:
1. **Short-term memory** — the current conversation (last N messages).
2. **Long-term memory** — stable user preferences, project context, decisions.

## Why it exists

Without memory, every query is independent. The system cannot:
- Remember that the user prefers bullet points.
- Recall that the user is working on Project X.
- Build on previous turns in a conversation.

## How it works (in this project)

### Short-term

Backed by the `messages` table. On each turn, load the last N (default 10) messages and include them in the generator context.

### Long-term

Backed by the `memories` table. Each memory has:
- `user_id` — always the owner
- `scope` — user_pref | project_context | recurring_question | decision
- `content` — the memory text
- `confidence` — 0..1
- `expires_at` — optional expiry
- `superseded_by` — for conflict resolution

After each assistant turn, an LLM call extracts candidate memories. An LLM-judge filters out trivial things. New memories that conflict with existing ones mark the old ones as `superseded_by`.

## Where it appears in the code

- Short-term: `src/memory/short_term.py`
- Long-term: `src/memory/long_term.py`
- Retrieval: `src/memory/retrieval.py`
- Extraction prompt: `prompts/v1/memory_extraction.md`
- API: `apps/api/app/routers/memory.py`

## Trade-offs

### Memory in document_chunks vs. separate table

- In chunks: one retrieval path. But pollutes corpus, hard to enforce `user_id` filter, mixes with citations.
- Separate table: clean separation, `user_id` filter is trivial, different lifecycle.

We chose separate. See ADR-005.

### LLM extraction vs. explicit user input

- LLM extraction: automatic, captures implicit preferences. Risk: stores trivial things.
- Explicit: user adds memories manually. Risk: users don't bother.

We use both — LLM extraction with strict filtering, plus explicit `/memory` API for user control.

## Failure modes

- **Memory pollution** — too many low-value memories. Mitigated by strict extraction prompt + confidence scoring + max per user.
- **Conflicting memories** — "user prefers dark mode" + "user prefers light mode". Mitigated by `superseded_by` — new memory marks old as superseded.
- **Cross-user leakage** — user A sees user B's memories. Mitigated by `user_id` filter always.
- **Expired memories retrieved** — old data leaks in. Mitigated by `expires_at` filter.

## Further reading

- Mem0, "Memory for AI Agents" — open-source memory framework
- Park et al., "Generative Agents: Interactive Simulacra of Human Behavior" (2023)
