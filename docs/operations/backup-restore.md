# Backup & Restore

## What to back up

1. **Postgres database** — all data (documents, chunks, embeddings, conversations, memories, audit logs, evaluations).
2. **S3 bucket (original files)** — original PDFs, markdown, etc.
3. **Langfuse Postgres** — trace history (optional but recommended).
4. **Configuration** — `.env`, `configs/*/config.yaml`. Stored in git for non-secrets; secrets in your secrets manager.

## Backup schedule

| Component        | Frequency | Retention | Storage                |
| ---------------- | --------- | --------- | ---------------------- |
| Postgres (prod)  | Hourly    | 7 days    | S3 with versioning     |
| Postgres (prod)  | Nightly   | 30 days   | S3, transition to Glacier after 7 days |
| Postgres (prod)  | Weekly    | 1 year    | S3 Glacier             |
| S3 (originals)   | Continuous (S3 versioning) | 90 days | S3 |
| Langfuse         | Nightly   | 30 days   | S3                     |

## Backup procedure

### Automated (cron on the VM)

```cron
# Hourly Postgres backup
0 * * * * cd /opt/agentic-rag && docker compose exec -T postgres pg_dump -U rag rag | gzip > /opt/backups/hourly/rag-$(date +\%Y\%m\%d-\%H).sql.gz && aws s3 cp /opt/backups/hourly/rag-$(date +\%Y\%m\%d-\%H).sql.gz s3://your-bucket/agentic-rag/prod/hourly/ && find /opt/backups/hourly -mtime +1 -delete

# Nightly Postgres backup (long retention)
0 2 * * * cd /opt/agentic-rag && docker compose exec -T postgres pg_dump -U rag rag | gzip > /opt/backups/daily/rag-$(date +\%Y\%m\%d).sql.gz && aws s3 cp /opt/backups/daily/rag-$(date +\%Y\%m\%d).sql.gz s3://your-bucket/agentic-rag/prod/daily/ && find /opt/backups/daily -mtime +30 -delete
```

### Manual (one-off)

```bash
docker compose exec -T postgres pg_dump -U rag rag > backup-$(date +%Y%m%d).sql
gzip backup-*.sql
aws s3 cp backup-*.sql.gz s3://your-bucket/agentic-rag/manual/
```

## Restore procedure

### Restore from S3 backup

```bash
# 1. Download the backup
aws s3 cp s3://your-bucket/agentic-rag/prod/daily/rag-2025-01-15.sql.gz .

# 2. Decompress
gunzip rag-2025-01-15.sql.gz

# 3. Stop the API (avoid writes during restore)
docker compose stop api worker

# 4. Drop and recreate the database
docker compose exec postgres psql -U rag -c "DROP DATABASE IF EXISTS rag;"
docker compose exec postgres psql -U rag -c "CREATE DATABASE rag OWNER rag;"

# 5. Restore
cat rag-2025-01-15.sql | docker compose exec -T postgres psql -U rag -d rag

# 6. Re-apply extensions
docker compose exec postgres psql -U rag -d rag -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE SCHEMA IF NOT EXISTS rag;"

# 7. Restart the API
docker compose start api worker

# 8. Verify
curl http://localhost:8000/health/ready
docker compose exec postgres psql -U rag -d rag -c "SELECT count(*) FROM documents;"
```

### Point-in-time recovery (managed Postgres only)

If you're on RDS / Cloud SQL, use the built-in point-in-time recovery:

1. AWS Console → RDS → Actions → Restore to point in time.
2. Select the timestamp.
3. Create a new RDS instance.
4. Switch the app to point at the new instance.

## Restore drill (monthly)

Once a month, in staging:

1. Pick a random backup from the past week.
2. Restore it to a fresh VM.
3. Verify the app starts and serves queries correctly.
4. Verify document count matches production.
5. Document any issues.

A backup you've never restored is not a backup.

## RPO and RTO

- **RPO (Recovery Point Objective)**: 1 hour (hourly backups).
- **RTO (Recovery Time Objective)**: 1 hour (manual restore procedure).
- For tighter RPO/RTO, use managed Postgres with point-in-time recovery (RPO: 5 minutes) and a hot standby (RTO: 5 minutes).
