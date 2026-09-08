# Agentic RAG vs. Pipeline RAG

## Concept

**Pipeline RAG** is a fixed sequence: retrieve → generate → respond. Every query follows the same path.

**Agentic RAG** is a stateful loop: classify → plan → (retrieve → validate → maybe retrieve more) → generate → verify citations → respond. The path adapts to the query.

## Why agentic exists

Some queries cannot be answered in a single retrieval pass:

```
User: "Summarize what changed in Project X during Q2 and identify the major risks."
```

This requires:
1. Retrieve Project X's original objectives.
2. Retrieve Q2 work completed.
3. Retrieve Q2 incidents.
4. Retrieve current risks.
5. Synthesize across all four.

A pipeline would do one retrieval and miss 3 of the 4 needed pieces. An agent decomposes the query into 4 sub-questions and retrieves each.

## When to use agentic vs. pipeline

| Query type          | Strategy              |
| ------------------- | --------------------- |
| Simple factual      | Pipeline (single retrieval) |
| Comparative         | Pipeline (with multi-entity retrieval) |
| Temporal            | Agentic (date filtering + version comparison) |
| Multi-hop           | Agentic (decomposition required) |
| Analytical          | Agentic (multi-source synthesis) |
| Unsupported         | Agentic (classify + abstain immediately) |

In this system, the **classifier** (`src/agents/classifier.py`) routes simple queries through a single-retrieval path and complex queries through the full agent loop.

## How it works (in this project)

```
User query
  ↓
Classify (simple / comparative / temporal / multi-hop / analytical / unsupported)
  ↓
If unsupported → abstain
  ↓
Plan (decompose into sub-questions + tool assignments)
  ↓
For each sub-question:
    ├→ Tool call (search_documents / search_by_date / memory_search / ...)
    ├→ Retrieve (hybrid + rerank)
    └→ Add to evidence pool
  ↓
Evidence sufficiency check (LLM-judge)
  ↓
If insufficient AND budget remains → retrieve more
  ↓
Generate answer with [N] citation markers
  ↓
Validate citations (LLM-judge)
  ↓
If all citations invalid → withhold response (HALLUCINATION_DETECTED)
  ↓
Final answer + citations
```

## Termination conditions

The agent MUST NOT recurse forever. Hard limits:

| Limit                | Default | Where enforced                       |
| -------------------- | ------- | ------------------------------------ |
| `max_steps`          | 8       | `AgentState.can_continue()`          |
| `max_tool_calls`     | 10      | `AgentState.can_continue()`          |
| `global_timeout_s`   | 30      | `asyncio.timeout()` in `run_agent()` |
| Loop detection       | n/a     | `AgentState.is_looping()`            |

Loop detection: if the same `(tool, args_hash)` appears in the last 2 tool calls, abort with `AGENT_LOOP`.

## Where it appears in the code

- State machine: `src/agents/state.py`
- Classifier: `src/agents/classifier.py`
- Planner: `src/agents/planner.py`
- Orchestrator (the loop): `src/agents/orchestrator.py`
- Tools: `src/agents/tools/`
- Termination: enforced throughout

## Trade-offs

### Agentic vs. pipeline

- Agentic: handles complex queries; can abstain intelligently; explains its reasoning.
- Pipeline: faster (1 LLM call vs. 4-6); cheaper; easier to debug.

For our mix of queries (~40% simple, ~30% multi-hop, ~20% temporal, ~10% unsupported), agentic is worth the cost. For a pure FAQ bot, pipeline would suffice.

### Custom state machine vs. LangGraph

- Custom: full control; no dependency; ~200 lines of code.
- LangGraph: built-in check-pointing; opinionated state model; significant dependency.

We chose custom (see ADR-004). The agent loop is simple enough that a framework adds complexity without value.

## Failure modes

- **Infinite loop** → mitigated by `max_steps`, `max_tool_calls`, `global_timeout_s`, and loop detection.
- **Planner generates too many sub-questions** → mitigated by `max_tool_calls=10`.
- **LLM-judge says evidence is insufficient forever** → mitigated by `max_steps` (the agent gives up and abstains).
- **Tool fails** → mitigated by `try/except` in the loop; failure is recorded and the agent continues or aborts.

## Experiment results

See `evals/reports/comparison.md` — Baseline 6 (agentic) vs. Baseline 5 (hybrid+rerank, no agent). **Replace placeholders with real measurements.**

## Further reading

- Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection" (2023)
- Yoran et al., "Answering Questions by Meta-Reasoning across Multiple Paragraphs" (2023)
