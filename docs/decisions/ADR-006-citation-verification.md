# ADR-006: Citation verification (LLM-judge)

- **Status**: Accepted
- **Date**: 2025-01-01

## Context

The LLM generates answers with inline `[N]` citation markers. Naively trusting these markers (i.e., assuming the cited chunk supports the claim) leads to "grounded-looking" hallucinations: the LLM cites a chunk that exists but does not actually support the claim.

## Problem

Decide whether to trust the LLM's citations or validate them.

## Options considered

### Option A: Trust the LLM's citations

- Pros: zero extra latency; zero extra cost.
- Cons: hallucinated citations; user trust erodes when they click a citation and find it doesn't support the claim.

### Option B: Heuristic check (e.g., claim and chunk must share N tokens)

- Pros: fast; no API call.
- Cons: brittle; high false-positive and false-negative rates.

### Option C: LLM-judge citation verification

- Pros: high accuracy; can detect partial support, contradictions, hallucinated facts.
- Cons: extra LLM call (~200ms, ~$0.0001/call); adds dependency on judge model.

## Decision

**Option C: LLM-judge citation verification.**

## Rationale

- Citation correctness is a core product feature. "Here is the answer, and here is why the system believes it" requires verifiable citations.
- The cost is acceptable: ~$0.0001 per query for the verification call.
- The latency is acceptable: ~200ms added to a ~3s query.

## Trade-offs

- Extra LLM call adds latency and cost.
- LLM-judge has its own biases; we calibrate it against 20 hand-labeled examples.

## Consequences

- After generation, `validate_citations()` runs an LLM-judge over each (claim, cited chunk) pair.
- Citations the judge marks as unsupported are dropped from the response.
- If all citations are dropped, the answer is withheld with `HALLUCINATION_DETECTED` failure.

## What happens if this component fails?

- If the LLM-judge fails (API error), we conservatively drop all citations and return the answer with `confidence=low`.

## How would we replace it later?

- Could swap to a fine-tuned small model for the judge, or to a deterministic NLI (natural language inference) model.
