# Production-Grade Agentic RAG Platform

> A reproducible, evaluated, secured, observable, and deployable **Agentic Retrieval-Augmented Generation (RAG)** platform for continuously changing organizational knowledge.

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## What is this?

A serious, portfolio-grade Agentic RAG system designed to be defensible in a senior AI Engineer / ML Engineer interview. It demonstrates:

- **Hybrid retrieval** (dense + lexical) with Reciprocal Rank Fusion
- **Cross-encoder reranking** (BGE-reranker-v2-m3)
- **Agentic orchestration** with planning, query decomposition, multi-step retrieval, and termination conditions
- **Persistent memory** (short-term + long-term, with expiry, conflict resolution, and audit trail)
- **Document freshness awareness** with version metadata and effective-date logic
- **RBAC enforced at the SQL layer** (pre-retrieval filtering)
- **Citation engine** with validation against retrieved evidence
- **Reproducible evaluation** with golden dataset, baselines, and CI quality gates
- **Observability** via OpenTelemetry + Langfuse
- **Failure handling** with explicit failure states and user-friendly messages
- **Security hardening** against prompt injection, retrieval poisoning, and unauthorized access
- **Production deployment** with Docker, CI/CD, backups, and rollback

---

## What this is NOT

- Not a "ChatGPT wrapper"
- Not a LangChain demo
- Not a toy app that uploads a PDF and answers questions

---

## Quickstart

```bash
# 1. Clone and enter
git clone <your-repo-url> agentic-rag-platform
cd agentic-rag-platform

# 2. Copy and fill in environment
cp .env.example .env
# Edit .env with your OpenAI / Hugging Face / Langfuse credentials

# 3. Bring up the stack
make up              # docker compose up -d (postgres, api, web, worker, langfuse)
make migrate         # alembic upgrade head
make seed            # load demo users, roles, departments

# 4. Ingest sample documents
make ingest-local    # ingests data/sources/local/

# 5. Run the API and frontend
open http://localhost:3000   # Next.js web UI
open http://localhost:8000/docs  # FastAPI docs
```

See **[QUICKSTART.md](QUICKSTART.md)** for the full walkthrough and **[STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md)** for the complete 14-day build guide.

---

## Architecture (one-paragraph version)

User → Next.js frontend → FastAPI `/query` endpoint → Agent Orchestrator (custom state machine) → Planner (LLM) → Tool calls (`search_documents`, `search_by_date`, `memory_search`, ...) → Hybrid retrieval (dense via pgvector + lexical via Postgres FTS, fused with RRF) → Cross-encoder reranking → Evidence sufficiency check → LLM generation with citation markers → Citation validation → Response with citations + trace_id. PostgreSQL stores documents, chunks, embeddings, conversations, memories, evaluations, audit logs. OpenTelemetry exports traces to Langfuse. RBAC is enforced in the retrieval SQL `WHERE` clause, not after retrieval.

Full architecture diagrams in [`docs/architecture/`](docs/architecture/).

---

## Repository layout

```
.
├── apps/
│   ├── api/                   # FastAPI backend
│   └── web/                   # Next.js 14 frontend
├── src/                       # Backend library code
│   ├── ingestion/             # Fetchers, parsers, cleaners, chunkers, indexer
│   ├── retrieval/             # Dense, lexical, hybrid, freshness
│   ├── reranking/             # Cross-encoder reranker
│   ├── agents/                # State machine, planner, classifier, tools
│   ├── memory/                # Short-term, long-term, retrieval
│   ├── citations/             # Builder + validator
│   ├── security/              # RBAC, prompt injection, audit
│   ├── evaluation/            # Metrics + runner
│   ├── observability/         # Tracing, metrics, logging, cost
│   ├── tools/                 # Tool registry
│   └── core/                  # DB, config, failures, retries
├── tests/                     # Unit, integration, retrieval, agent, security, evaluation, e2e
├── evals/                     # Golden dataset, baselines, experiments, reports
├── prompts/                   # Versioned prompt files (v1, v2, ...)
├── configs/                   # YAML configs (base, dev, staging, prod)
├── scripts/                   # Operational scripts (ingest, migrate, eval, bench)
├── docs/                      # Architecture, research, product, decisions, learning, security
├── infra/                     # docker-compose.prod.yml, k8s/, terraform/
├── docker/                    # Dockerfiles for api, web, worker
├── .github/workflows/         # CI/CD
├── alembic/                   # DB migrations
├── Makefile                   # All common commands
├── pyproject.toml             # Python project config
├── docker-compose.yml         # Local dev stack
├── .env.example               # Environment template
└── .gitignore
```

---

## Common commands

| Command              | What it does                                              |
| -------------------- | -------------------------------------------------------- |
| `make up`            | Start all services (postgres, api, web, worker, langfuse)|
| `make down`          | Stop all services                                         |
| `make migrate`       | Apply DB migrations                                       |
| `make seed`          | Load demo users, roles, departments                       |
| `make ingest-local`  | Ingest documents from `data/sources/local/`               |
| `make test`          | Run unit + integration tests                              |
| `make eval`          | Run full evaluation on the golden dataset                 |
| `make eval-smoke`    | Run 10-item smoke eval (used in CI)                       |
| `make eval-compare`  | Generate `evals/reports/comparison.md` across baselines   |
| `make lint`          | ruff + black --check + mypy                               |
| `make format`        | ruff --fix + black                                        |
| `make bench`         | Run performance benchmarks                                |
| `make db-reset`      | Drop + recreate + migrate + seed (DESTRUCTIVE)            |

---

## Documentation map

| You want to...                      | Read this                                                |
| ----------------------------------- | -------------------------------------------------------- |
| Get started in 10 minutes           | [QUICKSTART.md](QUICKSTART.md)                           |
| Build this from scratch             | [STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md)           |
| Understand the architecture         | [docs/architecture/system-design.md](docs/architecture/system-design.md) |
| Understand a design decision        | [docs/decisions/](docs/decisions/)                       |
| See measured results                | [evals/reports/comparison.md](evals/reports/comparison.md) |
| Operate the system                  | [docs/operations/](docs/operations/)                     |
| Learn RAG concepts                  | [docs/learning/](docs/learning/)                         |
| Review the security model           | [docs/security/](docs/security/)                         |
| Prepare for an interview            | [docs/career/interview-guide.md](docs/career/interview-guide.md) |

---

## Tech stack (summary)

| Concern            | Choice                                  |
| ------------------ | --------------------------------------- |
| Backend            | Python 3.11, FastAPI, Pydantic v2       |
| Database           | PostgreSQL 16 + pgvector 0.7            |
| Embeddings         | `BAAI/bge-m3` (local) or OpenAI         |
| Reranker           | `BAAI/bge-reranker-v2-m3`               |
| Orchestration      | Custom state machine (no LangGraph)     |
| LLM                | OpenAI `gpt-4o-mini` + provider abstraction |
| Frontend           | Next.js 14, Tailwind, shadcn/ui         |
| Observability      | OpenTelemetry + Langfuse (self-hosted)  |
| CI                 | GitHub Actions                          |
| Containers         | Docker + Compose                        |

Full rationale in [`docs/research/technology-selection.md`](docs/research/technology-selection.md).

---

## License

MIT. See [LICENSE](LICENSE).
