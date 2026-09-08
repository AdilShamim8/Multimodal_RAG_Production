# ADR-004: Custom agent state machine (not LangGraph)

- **Status**: Accepted
- **Date**: 2025-01-01

## Context

We need to orchestrate an agentic RAG loop: classify → plan → retrieve (possibly multiple times) → validate → generate → verify citations. This requires a stateful loop with termination conditions, loop detection, and timeouts.

## Problem

Choose between building a custom state machine, using LangGraph, or using another orchestration framework (e.g., CrewAI, AutoGen).

## Options considered

### Option A: Custom state machine

- Pros: full control over loop semantics, termination, retries; no external dependency; minimal abstraction.
- Cons: we maintain the orchestration code ourselves.

### Option B: LangGraph

- Pros: popular; handles state graph compilation; has check-pointing.
- Cons: heavyweight; opinionated about state shape; adds a significant dependency; debugging requires understanding LangGraph internals.

### Option C: CrewAI / AutoGen

- Pros: multi-agent patterns out of the box.
- Cons: we don't need multi-agent; introduces significant abstractions for a single-agent loop.

## Decision

**Option A: Custom state machine.**

## Rationale

- The agent loop is conceptually simple: a while-loop with termination conditions.
- Adding LangGraph would tie us to its state model and versioning.
- Custom code is ~200 lines and trivially debuggable.
- We avoid a major dependency for a problem we can solve ourselves.

## Trade-offs

- We give up LangGraph's check-pointing (resumable state). For our use case (sub-30s queries), this is unnecessary.
- We must implement loop detection, timeouts, and retry policies ourselves.

## Consequences

- `src/agents/orchestrator.py` is the single entrypoint.
- `src/agents/state.py` defines `AgentState` with `is_terminal()`, `can_continue()`, `is_looping()`, `force_terminal()`.
- All transitions are explicit in `_run_loop()`.

## What happens if this component fails?

- If the orchestrator raises, the request handler catches it and returns a graceful failure response.
- Loop detection and timeouts prevent runaway execution.

## How would we replace it later?

- If we needed multi-agent or check-pointing, we could swap `run_agent()` for a LangGraph implementation, keeping the same input/output contract.
- The rest of the system (retrieval, memory, citations) is independent of the orchestrator choice.
