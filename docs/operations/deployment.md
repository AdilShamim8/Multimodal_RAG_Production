# Deployment Guide

> Step-by-step deployment for dev / staging / production environments.

## Dev (single machine)

```bash
git clone <repo> agentic-rag-platform
cd agentic-rag-platform
cp .env.example .env
# Edit .env with real keys
make up
make migrate
make seed
make ingest-local
```

Verify:
- http://localhost:8000/health → `{"status":"ok",...}`
- http://localhost:3000 → web UI loads
- http://localhost:3001 → Langfuse UI

## Staging (single VM)

Provision a VM with:
- 4 vCPU, 16 GB RAM, 100 GB SSD
- Ubuntu 22.04 LTS
- Docker + Docker Compose v2

```bash
# SSH into the VM
git clone <repo> /opt/agentic-rag
cd /opt/agentic-rag
cp .env.example .env
# Edit .env — use strong secrets (openssl rand -hex 32)
# Use staging config:
cp configs/staging/config.yaml configs/base/config.yaml

docker compose -f docker-compose.yml -f infra/docker-compose.staging.yml up -d
docker compose exec api python -m alembic upgrade head
docker compose exec api python -m scripts.seed
```

### Nightly backups

Add to cron on the VM:

```cron
0 2 * * * cd /opt/agentic-rag && docker compose exec -T postgres pg_dump -U rag rag | gzip > /opt/backups/rag-$(date +\%Y\%m\%d).sql.gz && aws s3 cp /opt/backups/rag-$(date +\%Y\%m\%d).sql.gz s3://your-backup-bucket/agentic-rag/staging/
```

Retain 30 days.

### Log aggregation

- Configure Docker logging driver to `json-file` with rotation:
  ```json
  {
    "log-driver": "json-file",
    "log-opts": {"max-size": "100m", "max-file": "10"}
  }
  ```
- Ship logs to your log aggregator (Loki, ELK, CloudWatch) via Fluent Bit.

## Production (HA VM pair or Kubernetes)

### Option A: HA VM pair with Docker Compose

- Two VMs behind a load balancer (NGINX, ALB, Cloud Load Balancer).
- Each VM runs the full stack (api, web, worker).
- Postgres on managed RDS / Cloud SQL (NOT on the VMs).
- S3 for object storage (original document files).
- Langfuse on a dedicated VM (or use Langfuse Cloud).
- Blue/green: deploy to VM A, verify, switch traffic, deploy to VM B.

### Option B: Kubernetes

Manifests in `infra/k8s/`:

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -k infra/k8s/
```

Includes:
- `Deployment` for api, web, worker (3 replicas each)
- `Service` for api (ClusterIP) and web (ClusterIP)
- `Ingress` for web (TLS termination)
- `HorizontalPodAutoscaler` for api (CPU > 70%)
- `PodDisruptionBudget` for api (min available: 2)
- `Secret` for env vars (populate from external secrets manager)

### Database

- Use managed Postgres (RDS, Cloud SQL, Aurora).
- Enable automated backups (7-day retention).
- Enable point-in-time recovery.
- Provision IOPS based on benchmark results.
- Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`

### Object storage

- S3 bucket for original document files.
- S3 bucket for database backups.
- Lifecycle policy: transition backups to Glacier after 30 days, delete after 1 year.

### Secrets

- Use AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault.
- NEVER commit secrets to git.
- The app reads secrets from env vars; the orchestrator injects them from the secrets manager.

### Rollback

1. **Application rollback**: deploy previous Docker image tag.
2. **Database rollback**: `alembic downgrade -1` (every migration has a tested `downgrade()`).
3. **Prompt rollback**: edit config to point `prompt_version` at the previous version (`v1` instead of `v2`). No redeploy needed.

### Health checks

- `/health` — liveness probe (always 200 if process alive).
- `/health/ready` — readiness probe (checks DB, embedder, LLM, reranker).
- Configure load balancer to use `/health/ready`.

## Post-deploy verification

After every deploy:

1. `curl https://your-domain/health/ready` returns 200 with all subsystems `ok`.
2. Run `make eval-smoke` against the production endpoint — faithfulness ≥ 0.85.
3. Submit a test query as `alice@demo.dev` — verify answer + citations.
4. Check Langfuse — verify traces are arriving.
5. Check Prometheus — verify `rag_query_total` is incrementing.

## Rollback drill (monthly)

Once a month, in staging:

1. Deploy v1.
2. Deploy v2.
3. Rollback to v1.
4. Verify rollback succeeds (queries work, no errors).
5. Document any issues.

A rollback you've never tested is not a rollback.
