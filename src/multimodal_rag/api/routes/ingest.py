"""/ingest endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter

from multimodal_rag.api.deps import ApiKeyDep, PipelineDep
from multimodal_rag.data import build_dataset_loader
from multimodal_rag.schemas import IngestRequest, IngestResponse

router = APIRouter(tags=["ingest"], prefix="/ingest")


@router.post("", response_model=IngestResponse)
def ingest(
    req: IngestRequest,
    pipeline: PipelineDep,
    _: ApiKeyDep = None,
) -> IngestResponse:
    """Ingest a dataset into the vector store.

    Sources:
    * ``sample`` — 200-recipe bundled sample (default)
    * ``hf``     — full HuggingFace 10k dataset (requires network + GPU for HF embedder)
    * ``local``  — load JSON from ``DATASET_LOCAL_PATH``
    """
    t0 = time.perf_counter()
    loader = build_dataset_loader()
    recipes = loader.load(source=req.source, limit=req.limit)
    n = pipeline.ingest(recipes)
    return IngestResponse(
        ingested=n,
        skipped=len(recipes) - n,
        duration_sec=time.perf_counter() - t0,
        dataset_source=req.source,
    )
