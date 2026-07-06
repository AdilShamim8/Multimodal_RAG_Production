"""/health endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from multimodal_rag._version import __version__
from multimodal_rag.api.deps import ApiKeyDep, PipelineDep, SettingsDep
from multimodal_rag.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    pipeline: PipelineDep,
    settings: SettingsDep,
    _: ApiKeyDep = None,
) -> HealthResponse:
    """Liveness/readiness probe."""
    return HealthResponse(
        status="ok" if pipeline.store.health() else "degraded",
        version=__version__,
        providers={
            "embedding": settings.embedding_provider,
            "reranker": settings.reranker_provider,
            "generator": settings.generator_provider,
        },
        vector_store=settings.vector_store,
        dataset_size=pipeline.store.count(),
    )


@router.get("/ready")
def readiness(pipeline: PipelineDep) -> dict:
    """Kubernetes-style readiness probe."""
    ok = pipeline.store.health()
    return {"ready": ok, "store": pipeline.store.name, "count": pipeline.store.count()}
