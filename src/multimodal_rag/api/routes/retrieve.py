"""/retrieve endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter

from multimodal_rag.api.deps import ApiKeyDep, PipelineDep
from multimodal_rag.exceptions import ValidationError
from multimodal_rag.pipeline.rag import _load_image_from_field
from multimodal_rag.schemas import RetrieveRequest, RetrieveResponse

router = APIRouter(tags=["retrieve"], prefix="/retrieve")


@router.post("", response_model=RetrieveResponse)
def retrieve(
    req: RetrieveRequest,
    pipeline: PipelineDep,
    _: ApiKeyDep = None,
) -> RetrieveResponse:
    """Retrieve ``top_k`` recipes for a text and/or image query."""
    if not req.query_text and not req.query_image:
        raise ValidationError("at least one of query_text or query_image is required")

    image = None
    if req.query_image:
        image = _load_image_from_field(req.query_image)

    t0 = time.perf_counter()
    results = pipeline.retrieve(
        query_text=req.query_text,
        query_image=image,
        top_k=req.top_k,
    )
    return RetrieveResponse(
        results=results,
        query_kind="text+image" if (req.query_text and image) else ("image" if image else "text"),
        elapsed_sec=time.perf_counter() - t0,
    )
