# What is RAG?

## Concept

Retrieval-Augmented Generation (RAG) is a pattern that combines a retriever (which finds relevant documents) with a generator (which produces an answer) so that the generator can ground its answer in the retrieved documents.

The alternative is "closed-book" generation — the LLM answers from its training data alone. Closed-book generation:
- Cannot answer questions about your private documents.
- Has a training-data cutoff date.
- Hallucinates confidently when it doesn't know.

RAG solves all three by:
1. Retrieving relevant chunks from your document corpus.
2. Placing those chunks in the LLM context.
3. Asking the LLM to answer based ONLY on those chunks.

## Why it exists

LLMs are trained on public data up to a cutoff date. They cannot, by themselves, answer:
- "What is our remote work policy?" (private document)
- "What changed in Q2 2025?" (after training cutoff)
- "What is the latest version of POL-2024-007?" (specific document)

RAG bridges the gap between general LLMs and private/real-time knowledge.

## How it works (in this project)

```
User query
  ↓
Embed query → vector
  ↓
Dense retrieval (pgvector cosine) + Lexical retrieval (Postgres FTS)
  ↓
Reciprocal Rank Fusion (RRF)
  ↓
Cross-encoder reranking (BGE-reranker-v2-m3)
  ↓
Top K evidence chunks
  ↓
LLM generation (with [N] citation markers)
  ↓
Citation validation
  ↓
Final answer + citations
```

## Where it appears in the code

- Retrieval: `src/retrieval/engine.py`
- Generation: `src/agents/generator.py`
- Citation validation: `src/agents/citation_validator.py`
- End-to-end: `apps/api/app/services/query_service.py`

## Trade-offs

### RAG vs. fine-tuning

- RAG: retrieve at inference time; no model training; easy to update knowledge.
- Fine-tuning: bake knowledge into model weights; expensive to update; better for style/tone.

For organizational knowledge that changes constantly, RAG is the right choice.

### RAG vs. long-context LLMs

- Long-context LLMs (e.g., Gemini 1.5 with 2M tokens) can swallow an entire corpus per query.
- RAG retrieves only the relevant chunks, keeping context small.

Trade-off: long-context is simpler but more expensive per query and slower. RAG is more complex but cheaper and faster. For corpora > 100k tokens, RAG wins on cost and latency.

## Failure modes

- **No relevant chunks retrieved** → "I couldn't find any documents matching your question."
- **Irrelevant chunks retrieved** → wrong answer or hallucination.
- **Conflicting chunks retrieved** → must be reported explicitly, not silently resolved.
- **LLM ignores retrieved chunks** → "grounded-looking" hallucination. Mitigation: citation validation.

## Experiment results

See `evals/reports/comparison.md` for measured Recall@K, faithfulness, and hallucination rate across our 6 baselines. **Do not fabricate.** Replace placeholders with real measurements.

## Further reading

- Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (2020) — the original RAG paper.
- Anthropic, "Contextual Retrieval" (2024) — modern best practices.
- Pinecone, "RAG Field Guide" — practical patterns.
