"""/generate endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter

from multimodal_rag.api.deps import ApiKeyDep, PipelineDep
from multimodal_rag.schemas import GenerateRequest, GenerateResponse

router = APIRouter(tags=["generate"], prefix="/generate")


@router.post("", response_model=GenerateResponse)
def generate(
    req: GenerateRequest,
    pipeline: PipelineDep,
    _: ApiKeyDep = None,
) -> GenerateResponse:
    """Generate a summary over the supplied recipes."""
    t0 = time.perf_counter()
    text = pipeline.generate(
        query=req.query,
        recipes=req.recipes,
        style=req.style,
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
    )
    return GenerateResponse(
        text=text,
        model=pipeline.generator.model_id,
        elapsed_sec=time.perf_counter() - t0,
    )
