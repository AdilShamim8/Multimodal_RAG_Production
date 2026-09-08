# ADR-001: PostgreSQL + pgvector for vector storage

- **Status**: Accepted
- **Date**: 2025-01-01

## Context

We need a storage layer for document chunks + their embeddings + metadata. We also need lexical (full-text) search on the same chunks. The system must support RBAC-aware retrieval (filtering by access policy in the WHERE clause, before the vector search).

## Problem

Choose between a dedicated vector database (Pinecone, Weaviate, Qdrant, Milvus) vs. PostgreSQL with the pgvector extension.

## Options considered

### Option A: Dedicated vector DB (Pinecone / Weaviate / Qdrant)

- Pros: purpose-built for vector search; HNSW out of the box; very fast at scale.
- Cons: introduces a second datastore; access policy filtering is awkward (most vector DBs filter post-retrieval); extra operational burden; harder transactions across relational + vector data.

### Option B: PostgreSQL + pgvector

- Pros: single datastore; ACID transactions across relational + vector; native `tsvector` for FTS in the same query; access policy filtering in the WHERE clause (pre-retrieval) is trivial; well-understood operations (backup, replication, monitoring).
- Cons: pgvector's HNSW is newer than dedicated DBs; very large corpora (>10M chunks) may need sharding.

### Option C: Hybrid (Postgres for metadata + dedicated DB for vectors)

- Pros: best of both at extreme scale.
- Cons: two sources of truth; complex sync; harder RBAC enforcement.

## Decision

**Option B: PostgreSQL + pgvector.**

## Rationale

- Single datastore dramatically simplifies operations, backup, and RBAC enforcement.
- Access policy filtering in the WHERE clause (pre-retrieval) is critical for security; pgvector makes this trivial.
- For our scale (~100k–1M chunks per tenant), pgvector with ivfflat or HNSW is more than fast enough.
- We avoid a second datastore to learn, deploy, monitor, and pay for.

## Trade-offs

- We give up the raw ANN throughput of a purpose-built DB.
- If we ever exceed 10M chunks per tenant, we may need to revisit.

## Consequences

- All chunk data lives in `document_chunks` table.
- Vector index is `ivfflat` initially (lists = ~sqrt(N)); will migrate to `hnsw` if needed.
- Backup strategy is `pg_dump` of the whole database — simpler than coordinating two datastores.

## What happens if this component fails?

- Postgres is down → all queries fail. We rely on Postgres HA (managed RDS / Cloud SQL) + a read replica.
- pgvector extension missing → migrations fail loudly at startup.

## How would we replace it later?

- Migrate embeddings to a dedicated DB by:
  1. Add a sync worker that writes embeddings to the new DB.
  2. Run dual-write for a verification period.
  3. Switch reads to the new DB.
  4. Drop the `embedding` column from `document_chunks`.
- This is a non-trivial migration but well-documented in the pgvector → Qdrant path.
