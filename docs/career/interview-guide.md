# Interview Prep — Agentic RAG Platform

> Difficult questions you should be able to answer about this system. Answers reference the actual implementation.

## RAG

### Q: Why hybrid retrieval instead of just vector search?

Vector search handles semantic similarity but misses exact matches. A query for "CS-101" (a course code) won't necessarily retrieve the chunk that literally contains "CS-101" — embeddings don't always put codes close to their mention. Lexical search (Postgres FTS) catches exact matches but misses synonyms ("work-life balance" won't find "wellness program"). Hybrid retrieval combines both, fused with Reciprocal Rank Fusion (RRF). See ADR-002 and `src/retrieval/hybrid.py`.

### Q: Why embeddings? Why not just BM25?

Embeddings capture semantic similarity — they understand that "remote work policy" is similar to "telecommuting guidelines." BM25 only sees exact term overlap. For queries like "how does the company support work-life balance," BM25 fails because the document says "wellness program." See `docs/learning/embeddings.md`.

### Q: Why reranking?

Initial retrieval uses a bi-encoder (BGE-m3) that embeds query and chunk separately — fast but loses fine-grained query-chunk interaction. The reranker (BGE-reranker-v2-m3) is a cross-encoder that sees (query, chunk) jointly, capturing attention between query tokens and chunk tokens. We retrieve top 50 candidates fast, then rerank to top 5 accurately. See ADR-003 and `src/reranking/cross_encoder.py`.

### Q: Why not only vector search?

Vector search alone misses exact identifiers: course codes, policy numbers, employee IDs, dates. These are best served by lexical search. Hybrid retrieval combines both. See `docs/learning/hybrid-retrieval.md`.

### Q: Why this chunking strategy?

We compared 4 strategies: fixed-token, sliding-window, semantic, structure-aware. Structure-aware (split on headings first, then fixed-token within a section) won on Recall@K because it preserves semantic boundaries. See `evals/reports/chunking_comparison.md` for measured results and `src/ingestion/chunking.py` for the implementation.

## Systems

### Q: What becomes the bottleneck?

At our scale (~100k chunks), the reranker is the bottleneck — it's CPU-bound and takes ~340ms p95 for 50 candidate pairs on a 4-core machine. LLM generation is the second bottleneck (~1-2s depending on response length). Postgres retrieval is fast (~50ms).

### Q: How would this scale to 10 million documents?

Several changes:
1. Switch pgvector index from `ivfflat` to `hnsw` (better recall at scale).
2. Shard by tenant or department (each shard has its own Postgres instance).
3. Move the reranker to a dedicated worker pool (or GPU instance).
4. Use a managed vector DB (Pinecone, Qdrant Cloud) if Postgres can't keep up.
5. Cache embeddings in Redis (already done) and consider caching reranker scores for common (query, chunk) pairs.

### Q: How would you support multi-tenancy?

Add a `tenant_id` column to every table. Modify `access_matches()` to filter on `tenant_id` first. Each tenant's data is isolated at the SQL layer. For very large tenants, shard by `tenant_id`. Cache per-tenant. Rate-limit per-tenant.

### Q: How would you reduce latency?

1. Cache embeddings (already done) — saves ~50ms per query.
2. Cache reranker scores for common (query, chunk) pairs — would save ~300ms.
3. Use a smaller reranker (e.g., MiniLM) for queries that don't need high precision.
4. Stream the LLM response (already done in the frontend; backend would need SSE).
5. Parallelize the dense and lexical retrieval queries (already done).

## Agents

### Q: Why use an agent instead of a pipeline?

A pipeline (retrieve → generate → respond) works for simple factual queries. It fails for multi-hop queries like "Summarize what changed in Project X during Q2 and identify the major risks" — that requires 4 separate retrievals (objectives, completed work, incidents, risks) and synthesis. An agent can decompose the query, retrieve each piece, validate that the evidence is sufficient, and retrieve more if not. See `docs/learning/agentic-rag.md` and ADR-004.

### Q: How do you prevent infinite loops?

Three layers:
1. **Hard limits**: `max_steps=8`, `max_tool_calls=10`, `global_timeout_s=30` — enforced in `AgentState.can_continue()` and `asyncio.timeout()` in `run_agent()`.
2. **Loop detection**: `AgentState.is_looping()` checks if the same `(tool, args_hash)` appears in the last 2 tool calls. If so, abort with `AGENT_LOOP`.
3. **Evidence sufficiency check**: an LLM-judge asks "Does this evidence answer the question?" — if "no" and we have budget, retrieve more; if "no" and no budget, abstain.

### Q: When should the agent stop?

The agent stops when:
- It has generated an answer with verified citations (success).
- It has hit `max_steps` or `max_tool_calls` (forced abstention).
- It has hit `global_timeout_s` (forced abstention with `LLM_TIMEOUT`).
- Loop detection triggered (forced abstention with `AGENT_LOOP`).
- Evidence is insufficient and no budget remains (forced abstention with `INSUFFICIENT_EVIDENCE`).
- The classifier routed to `unsupported` (immediate abstention, no retrieval).

## Evaluation

### Q: How do you know the system improved?

By running the same golden dataset through 6 baselines and comparing metrics:
1. Naive RAG
2. Dense only
3. Lexical only
4. Hybrid (no rerank)
5. Hybrid + rerank
6. Full agentic

Each baseline's metrics (Recall@K, faithfulness, hallucination rate, etc.) are recorded in `evals/reports/comparison.md`. An improvement is real only if it shows up across multiple metrics on the same dataset.

### Q: What is Recall@K?

The fraction of relevant items that appear in the top K retrieved. If there are 3 relevant chunks for a query and 2 of them are in the top 10 retrieved, Recall@10 = 2/3 = 0.67. See `src/evaluation/retrieval_metrics.py`.

### Q: Why can generation look correct while retrieval is wrong?

The LLM is excellent at sounding confident. If you retrieve the wrong chunks, the LLM may still produce a fluent, plausible answer that's hallucinated. This is why we have:
1. Citation validation — verifies every claim has a supporting citation.
2. Hallucination rate metric — measures the fraction of unsupported claims.
3. Faithfulness metric (Ragas) — measures whether the answer is supported by the evidence.

## Security

### Q: How do you defend against prompt injection?

Layered defense (defense in depth):
1. **Input classifier** — regex check against 10 known patterns + LLM-judge for nuanced detection. Flagged queries are routed to a safe refusal template.
2. **Retrieved-content isolation** — chunks are wrapped in `<retrieved_document>` XML tags; system prompt explicitly says content inside these tags is data, never instructions.
3. **Output sanitizer** — scans the generated answer for the same 10 patterns. If found, the answer is replaced with a safe refusal and the original is logged for forensics.
4. **Tool argument validation** — every tool call's arguments are validated against the tool's JSON schema. The LLM cannot inject `top_k=10000` to exfiltrate the whole DB.

See `docs/security/prompt-injection.md`.

### Q: How do you enforce permissions during retrieval?

RBAC is enforced in the SQL `WHERE` clause, **before** the vector search:

```sql
WHERE rag.access_matches(d.access_policy, :user_role, :user_projects, :user_id)
```

This is the `access_matches()` Postgres function defined in `alembic/versions/0002_access_matches_function.py`. It returns true if:
- The policy is empty (public).
- The user is an administrator.
- The user's role is in `policy.roles`.
- The user has a project in `policy.projects`.
- The user's ID is in `policy.users`.

**Never retrieve-then-filter.** That leaks metadata in traces and breaks pagination. See ADR-008.

## Memory

### Q: What belongs in long-term memory?

Only stable, useful information:
- User preferences ("user wants bullet points")
- Project context ("user is working on Project X")
- Recurring questions ("user keeps asking about policy Y")
- Decisions ("we decided to use Postgres")

The LLM-judge filters out trivial things ("hello", "thanks") and transient state ("user is in a meeting today"). See `prompts/v1/memory_extraction.md`.

### Q: How do you avoid memory pollution?

Three defenses:
1. **Strict extraction prompt** — the LLM is told to reject > 50% of candidates.
2. **Confidence scoring** — each memory has a confidence (0..1). Low-confidence memories are evicted first.
3. **Expiry** — memories can have `expires_at`. Expired memories are not retrieved (but kept for audit).

## Production

### Q: How do you monitor quality after deployment?

Three layers:
1. **Smoke eval in CI** — every PR runs a 10-item smoke eval. If faithfulness < 0.85, the build fails.
2. **Nightly full eval** — every night, the full golden dataset runs against staging. Results are uploaded as a GitHub artifact.
3. **Production observability** — Prometheus metrics (`rag_query_total`, `rag_query_latency_seconds`, `rag_failure_total`) and Langfuse traces for every request.

If quality drops, we see it in the eval report before users notice.

### Q: How do you roll back a bad prompt?

Prompts are versioned in `prompts/v1/`, `prompts/v2/`. The active version is set in config. To roll back:
1. Edit `configs/prod/config.yaml` to point `prompt_version: v1` (instead of `v2`).
2. Restart the API (or hot-reload config).
3. Verify a sample query.

No code deploy needed. No DB migration needed.

### Q: What happens if the LLM provider goes down?

- The LLM call retries 3 times with exponential backoff (1s, 2s, 4s) — see `src/core/retries.py`.
- If all retries fail, the query returns `LLM_TIMEOUT` with a user-friendly message.
- The provider abstraction (`src/llm/provider.py`) means we can switch providers by changing one config value.
- For high-availability production, configure a fallback provider (e.g., primary: OpenAI, fallback: Anthropic).
