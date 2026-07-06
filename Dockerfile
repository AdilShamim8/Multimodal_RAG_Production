# syntax=docker/dockerfile:1.7
# =========================================================================
# Multimodal RAG Production — Docker image
# CPU-only by default. For GPU support, use the `:gpu` variant (see README).
# =========================================================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HUB_DISABLE_TELEMETRY=1

# System deps (libglib + libGL for Pillow; build tools for any source builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
        libglib2.0-0 \
        libgl1 \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install -e ".[dev]"

# Copy the rest
COPY tests ./tests
COPY scripts ./scripts
COPY data ./data
COPY docs ./docs

# Healthcheck hits the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:${APP_PORT:-8000}/health || exit 1

EXPOSE 8000

# Default to uvicorn; override in compose for workers, etc.
CMD ["sh", "-c", "uvicorn multimodal_rag.app:app --host 0.0.0.0 --port ${APP_PORT:-8000} --workers ${APP_WORKERS:-1}"]

# ---- GPU variant ----
# Build with: docker build --target gpu -t multimodal-rag:gpu .
FROM base AS gpu
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir transformers accelerate sentencepiece
