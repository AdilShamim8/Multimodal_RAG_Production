"""FastAPI application factory.

``uvicorn multimodal_rag.app:app`` is the canonical entry point. The app
wires up middleware, exception handlers, routes, and a Prometheus metrics
endpoint.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from multimodal_rag._version import __version__
from multimodal_rag.api.deps import get_settings_dep
from multimodal_rag.api.middleware import (
    MetricsMiddleware,
    StructlogMiddleware,
    register_exception_handlers,
)
from multimodal_rag.api.routes import generate, health, ingest, rag, rerank, retrieve
from multimodal_rag.config import get_settings
from multimodal_rag.logging import configure_logging
from multimodal_rag.monitoring import record_build_info
from multimodal_rag.rate_limit import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    s = get_settings()
    configure_logging(s)
    record_build_info(__version__, s.app_env)
    log.info(
        "startup",
        version=__version__,
        env=s.app_env,
        embedding=s.embedding_provider,
        reranker=s.reranker_provider,
        generator=s.generator_provider,
        vector_store=s.vector_store,
    )
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    """Application factory — used by tests + uvicorn."""
    s = get_settings()
    configure_logging(s)
    record_build_info(__version__, s.app_env)

    app = FastAPI(
        title="Multimodal RAG Production",
        description=(
            "Production-grade multimodal RAG pipeline: "
            "embed → retrieve → rerank → generate. "
            "Supports text + image queries, pluggable model providers, and "
            "Qdrant / Chroma / FAISS vector stores."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate-limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Logging + Prometheus
    app.add_middleware(StructlogMiddleware)
    app.add_middleware(MetricsMiddleware)

    # Routes
    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(retrieve.router)
    app.include_router(rerank.router)
    app.include_router(generate.router)
    app.include_router(rag.router)

    # Metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Root → docs
    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    # Exception handlers
    register_exception_handlers(app)

    log.info("app_created", version=__version__, env=s.app_env)
    return app


app = create_app()

# Keep symbols used by type-checkers
_ = get_settings_dep
