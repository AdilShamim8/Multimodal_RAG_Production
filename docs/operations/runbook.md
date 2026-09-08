# Runbook — Agentic RAG Platform

> What to do when things go wrong.

## Triage flow

1. Check `/health/ready` — is the system reporting degraded?
2. Check Prometheus alerts — which one is firing?
3. Check Langfuse — are traces arriving? Are they failing?
4. Check Docker logs — `docker compose logs --tail=200 api`.
5. Consult the table below.

## Common incidents

### High latency (p95 > 5s)

**Symptom**: Prometheus alert `RAGQueryLatencyHigh`.

**Possible causes**:
1. Reranker is slow (CPU-bound) — check `rag_rerank_latency` metric.
2. LLM provider is slow — check `rag_llm_latency` metric.
3. Postgres is slow — check `pg_stat_activity` for long-running queries.
4. Cold start — embedder/reranker model not loaded.

**Actions**:
- If reranker: scale horizontally (more API replicas), or move reranker to a separate worker, or reduce `candidate_count` in config.
- If LLM: check provider status page; consider switching provider via config.
- If Postgres: check for missing indexes, long-running queries, lock contention.
- If cold start: warm up models at app startup (TODO in `main.py`).

### High failure rate

**Symptom**: Prometheus alert `RAGFailureRateHigh`.

**Actions**:
1. Check which failure type is dominant: `rag_failure_total{failure_type="..."}`.
2. Consult the failure-specific section below.

### NO_DOCUMENTS spike

**Symptom**: Many queries returning "I couldn't find any documents matching your question."

**Actions**:
1. Check if ingestion is up to date: `SELECT count(*) FROM documents WHERE deleted_at IS NULL;`
2. Check if chunks exist: `SELECT count(*) FROM document_chunks;`
3. If chunks missing: re-run ingestion.
4. If chunks present: check if access policy is too restrictive.

### INSUFFICIENT_EVIDENCE spike

**Symptom**: Many queries returning "I don't have enough evidence to answer this confidently."

**Actions**:
1. Check if the corpus covers the topics being asked about.
2. Check if chunking strategy is appropriate (try `structure-aware` instead of `fixed`).
3. Check if `candidate_count` is too low (try increasing to 100).
4. Sample a few failing queries and inspect the retrieved chunks in Langfuse.

### LLM_TIMEOUT spike

**Symptom**: Many queries failing with "The model is taking too long."

**Actions**:
1. Check provider status page (OpenAI / Anthropic).
2. Check network connectivity from API container.
3. Consider switching to a faster model temporarily (gpt-4o-mini instead of gpt-4o).
4. If persistent, scale API replicas to absorb the slower responses.

### AGENT_LOOP spike

**Symptom**: Many queries failing with "I'm having trouble reasoning through this."

**Actions**:
1. Sample failing traces in Langfuse.
2. Identify which tool is being called repeatedly.
3. The loop detector is firing — investigate WHY the LLM keeps calling the same tool.
4. Likely cause: ambiguous planner prompt. Update `prompts/v1/planning.md` and add a regression test.

### HALLUCINATION_DETECTED spike

**Symptom**: Many queries failing with "I generated an answer I cannot verify."

**Actions**:
1. Sample failing traces in Langfuse.
2. Check if the citation validator LLM-judge is being too strict.
3. Check if the generator is producing claims not supported by evidence — likely a prompt regression.
4. If the validator is broken, temporarily lower the threshold in config.

### Postgres down

**Symptom**: `/health/ready` returns `db: fail`.

**Actions**:
1. Check `docker compose ps postgres` — is the container running?
2. Check `docker compose logs postgres` — any error messages?
3. If disk full: `docker compose exec postgres df -h` and clean up.
4. If corrupted: restore from last night's backup (see `docs/operations/backup-restore.md`).
5. If you're on managed Postgres (RDS): check the AWS/GCP console.

### Redis down

**Symptom**: Caching layer unavailable.

**Actions**:
1. The app should continue to work (cache is optional) but slower.
2. Restart Redis: `docker compose restart redis`.
3. If data corruption: `docker compose down redis && docker volume rm agentic-rag_redis_data && docker compose up -d redis`.

### Langfuse down

**Symptom**: Traces not appearing in Langfuse UI.

**Actions**:
1. The app should continue to work (tracing is non-blocking).
2. Check `docker compose ps langfuse` and `docker compose logs langfuse`.
3. If Langfuse Postgres is full: clean up old traces.

## Escalation

- **P0 (system down)**: page on-call engineer.
- **P1 (degraded)**: notify team in Slack, investigate within 1 hour.
- **P2 (single query failure)**: file a GitHub issue, investigate next business day.

## Post-incident

After every P0/P1:
1. Write a post-mortem in `docs/operations/post-mortems/YYYY-MM-DD-<incident>.md`.
2. Add monitoring/alerts that would have caught it earlier.
3. Add a regression test if applicable.
