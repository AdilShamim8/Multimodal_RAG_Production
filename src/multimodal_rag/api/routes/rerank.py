"""/rerank endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter

from multimodal_rag.api.deps import ApiKeyDep, PipelineDep
from multimodal_rag.schemas import RerankRequest, RerankResponse

router = APIRouter(tags=["rerank"], prefix="/rerank")


@router.post("", response_model=RerankResponse)
def rerank(
    req: RerankRequest,
    pipeline: PipelineDep,
    _: ApiKeyDep = None,
) -> RerankResponse:
    """Rerank a list of candidate recipes against a text query."""
    if not req.candidates:
        return RerankResponse(results=[], elapsed_sec=0.0)
    t0 = time.perf_counter()
    from multimodal_rag.schemas import RecipeWithScore

    candidates = [
        RecipeWithScore(recipe=r, score=0.0, rank=i)
        for i, r in enumerate(req.candidates)
    ]
    scored = pipeline.rerank(
        query_text=req.query_text,
        candidates=candidates,
        top_k=req.top_k,
    )
    return RerankResponse(
        results=scored,
        elapsed_sec=time.perf_counter() - t0,
    )
