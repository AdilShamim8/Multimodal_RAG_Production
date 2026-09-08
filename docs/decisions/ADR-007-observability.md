# ADR-007: OpenTelemetry + Langfuse (not LangSmith)

- **Status**: Accepted
- **Date**: 2025-01-01

## Context

We need end-to-end tracing of every RAG query: classify → plan → retrieve → rerank → generate → validate. We also need metrics (latency, cost, failure rate) and structured logs.

## Problem

Choose an observability backend: LangSmith, Langfuse, or a custom OpenTelemetry stack.

## Options considered

### Option A: LangSmith (LangChain's hosted offering)

- Pros: tight LangChain integration; easy setup if you use LangChain.
- Cons: we don't use LangChain; per-trace cost; data leaves our infrastructure; vendor lock-in.

### Option B: Langfuse (self-hosted)

- Pros: open-source; self-hostable; OpenTelemetry-compatible; first-class support for LLM spans; free at our scale.
- Cons: we run it ourselves (but it's a single Docker container).

### Option C: Custom OpenTelemetry + Jaeger

- Pros: vendor-neutral; standard.
- Cons: no LLM-specific UI; we'd build the dashboards ourselves.

## Decision

**Option B: Langfuse (self-hosted), with OpenTelemetry as the wire protocol.**

## Rationale

- Self-hosting keeps data inside our infrastructure (important for enterprise).
- Langfuse has a great UI for LLM traces: token counts, cost, prompt versions, eval results.
- OpenTelemetry as the wire protocol means we can swap backends later without changing application code.
- Free at our scale.

## Trade-offs

- We run one more container (Langfuse).
- Langfuse's Postgres needs backups.

## Consequences

- `apps/api/app/observability/otel.py` exports OTLP to Langfuse.
- Every span has `trace_id`, `user_id`, `model`, `tokens_in`, `tokens_out`, `cost_usd` attributes.
- PII is redacted at the structlog layer before reaching Langfuse.

## What happens if this component fails?

- If Langfuse is down, traces are dropped (the BatchSpanProcessor buffers and silently discards on overflow). Application continues to work.
- We alert on Langfuse uptime via Prometheus.

## How would we replace it later?

- Switch the OTLP exporter endpoint to Jaeger, Honeycomb, Datadog, or LangSmith — no application code changes.
