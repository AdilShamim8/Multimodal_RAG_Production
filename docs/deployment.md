# Deployment guide

## 1. Local development

```bash
git clone <this-repo>
cd multimodal-rag-production
cp .env.example .env
make install           # CPU-only, mock providers
make ingest            # Load 200-sample dataset
make serve             # uvicorn on :8000
```

## 2. Docker (single container)

```bash
docker build -t multimodal-rag .
docker run -p 8000:8000 --env-file .env multimodal-rag
```

## 3. Docker Compose (full stack)

```bash
docker compose up -d
```

This starts five services:

| Service      | Port | Purpose                          |
|--------------|------|----------------------------------|
| `api`        | 8000 | FastAPI app                      |
| `qdrant`     | 6333 | Vector DB (REST)                 |
| `redis`      | 6379 | Future: distributed cache        |
| `prometheus` | 9090 | Metrics scraping                 |
| `grafana`    | 3000 | Dashboards (admin/admin)         |

Then set `VECTOR_STORE=qdrant` in `.env` and restart the API to point it at
Qdrant instead of the embedded Chroma.

## 4. GPU deployment

For real NVIDIA Nemotron + Qwen3-VL models:

```bash
docker build --target gpu -t multimodal-rag:gpu .
docker run --gpus all -p 8000:8000 --env-file .env \
    -e EMBEDDING_PROVIDER=local_hf \
    -e RERANKER_PROVIDER=local_hf \
    -e GENERATOR_PROVIDER=local_hf \
    multimodal-rag:gpu
```

You also need to pre-download the model weights on first start:

```bash
docker exec -it <container> multimodal-rag download-models
```

## 5. Kubernetes (sketch)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multimodal-rag
spec:
  replicas: 3
  selector:
    matchLabels: { app: multimodal-rag }
  template:
    metadata:
      labels: { app: multimodal-rag }
    spec:
      containers:
        - name: api
          image: multimodal-rag:latest
          ports: [{ containerPort: 8000 }]
          envFrom: [{ secretRef: { name: mrag-secrets } }]
          readinessProbe:
            httpGet: { path: /ready, port: 8000 }
          livenessProbe:
            httpGet: { path: /health, port: 8000 }
          resources:
            requests: { cpu: 500m, memory: 1Gi }
            limits:   { cpu: 2000m, memory: 4Gi }
```

A `HorizontalPodAutoscaler` targeting CPU 70% and a `Service` of type
ClusterIP complete the typical setup.

## 6. Production checklist

- [ ] Set `APP_ENV=prod` (switches logs to JSON)
- [ ] Set a strong `API_KEY` and require it from clients
- [ ] Restrict `CORS_ORIGINS` to your real origins
- [ ] Use Qdrant (not embedded Chroma) for persistence + scale
- [ ] Run ≥3 replicas behind a load balancer
- [ ] Wire Prometheus → Grafana alerting on `multimodal_rag_errors_total`
- [ ] Set up periodic dataset re-ingest via `multimodal-rag ingest` cron
- [ ] For multi-GPU, run the embedder/generator behind a Triton / vLLM sidecar
