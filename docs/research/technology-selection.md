# Technology Selection

> Rationale for every major technology choice in this project.

## Summary table

| Concern            | Choice                                  | Why                                                                 |
| ------------------ | --------------------------------------- | ------------------------------------------------------------------- |
| Backend            | Python 3.11 + FastAPI                   | Async, typed, mature ecosystem                                      |
| Database           | PostgreSQL 16 + pgvector 0.7            | One DB for relational + vector + FTS; reduces moving parts          |
| Embeddings         | `BAAI/bge-m3` (local)                   | Multilingual, strong on MTEB, free                                  |
| Reranker           | `BAAI/bge-reranker-v2-m3`               | Cross-encoder, multilingual, self-hostable                          |
| Orchestration      | Custom state machine                    | Reduces dependencies; we control loop semantics                     |
| LLM                | OpenAI `gpt-4o-mini` + provider abstraction | Cheap + capable; swap via provider abstraction                  |
| Frontend           | Next.js 14 + Tailwind                   | Modern, SSR, good DX                                                |
| Observability      | OpenTelemetry + Langfuse (self-hosted)  | Own your traces; OTel for non-LLM spans                             |
| CI                 | GitHub Actions                          | Native to GitHub                                                    |
| Container          | Docker + Compose                        | Local + simple prod parity                                          |
| Caching            | Redis                                   | Standard, fast, well-supported                                      |
| Auth               | JWT (python-jose) + bcrypt (passlib)    | Stateless; standard library                                         |
| Migrations         | Alembic                                 | Standard SQLAlchemy migration tool                                  |
| Document parsing   | docling (PDF), trafilatura (HTML)       | Layout-aware PDF; clean HTML extraction                             |
| Evaluation         | Ragas + custom metrics                  | Ragas for faithfulness; custom for citation correctness             |
| Testing            | pytest + pytest-asyncio                 | Standard Python testing                                             |

## Detailed rationale

### Backend: Python 3.11 + FastAPI

- **Async**: required for concurrent LLM calls, DB queries, HTTP requests.
- **Typed**: Pydantic v2 + mypy strict mode catches bugs at dev time.
- **Mature ecosystem**: SQLAlchemy 2.0, asyncpg, httpx, structlog, OpenTelemetry — all production-grade.
- **FastAPI**: OpenAPI docs out of the box; dependency injection; async-native.

**Alternatives considered**: Go (faster but no ML ecosystem), Node.js (good for frontend but weaker ML tooling), Rust (overkill for this layer).

### Database: PostgreSQL 16 + pgvector

See ADR-001 for the full rationale. Key points:
- Single datastore for relational + vector + FTS.
- RBAC enforced in the WHERE clause (critical for security).
- ACID transactions across all data.
- Well-understood operations (backup, replication, monitoring).

**Alternatives considered**: Pinecone (managed vector DB), Weaviate, Qdrant, Milvus.

### Embeddings: BAAI/bge-m3

- Multilingual (handles English + non-English content).
- Top-tier on MTEB benchmark.
- Self-hostable (no per-call cost).
- 1024-dim (smaller than OpenAI's 3072-dim, faster retrieval).

**Alternatives considered**: OpenAI `text-embedding-3-large` (more expensive, vendor lock-in), Cohere Embed v3 (per-call cost), E5-large-v2 (English-only).

### Reranker: BGE-reranker-v2-m3

See ADR-003.

### Orchestration: Custom state machine

See ADR-004.

### LLM: OpenAI gpt-4o-mini

- Cheap ($0.00015/1k input, $0.0006/1k output — ~$0.0005 per query).
- Capable enough for grounded Q&A with citations.
- Provider abstraction (`src/llm/provider.py`) means we can swap to Anthropic or self-hosted vLLM by changing one config.

**Alternatives considered**: GPT-4o (more expensive, marginally better for our use case), Claude 3.5 Sonnet (per-call cost similar), Llama 3.1 70B self-hosted (ops overhead).

### Frontend: Next.js 14

- App Router with SSR for fast initial load.
- TypeScript throughout.
- Tailwind for styling; shadcn/ui for components (in production).
- Streaming responses via Server-Sent Events (TODO).

**Alternatives considered**: Remix (similar but smaller ecosystem), plain Vite + React (less SSR support), SvelteKit (smaller ecosystem).

### Observability: OpenTelemetry + Langfuse

See ADR-007.

### CI: GitHub Actions

- Native to GitHub (where the repo lives).
- Free tier sufficient for our PR checks.
- Self-hosted runners available if needed.

**Alternatives considered**: CircleCI (paid), GitLab CI (different VCS), Jenkins (self-hosted ops burden).

## What we explicitly rejected

### LangChain / LangGraph

Popular but opinionated. Adds significant abstraction for problems we can solve in 200 lines of code. The dependency cost outweighs the benefit at our scale. See ADR-004.

### LlamaIndex

Similar to LangChain — useful for demos but adds abstraction we don't need.

### Pinecone / Weaviate / Qdrant

Dedicated vector DBs introduce a second datastore, complicate RBAC enforcement, and add operational burden. pgvector handles our scale (100k–1M chunks per tenant) fine. See ADR-001.

### LangSmith

Per-trace cost; data leaves our infrastructure. Langfuse (self-hosted) is free at our scale and keeps data inside our network. See ADR-007.

### Celery / RQ

For background jobs, we use a simple asyncio worker (`scripts/worker.py`). Adds Celery/RQ only when we outgrow it.

### GraphQL

REST is sufficient for our API surface (10 endpoints). GraphQL's complexity is not justified.
