"""/rag endpoint — full end-to-end RAG query."""

from __future__ import annotations

from fastapi import APIRouter

from multimodal_rag.api.deps import ApiKeyDep, PipelineDep
from multimodal_rag.pipeline.rag import _load_image_from_field
from multimodal_rag.schemas import RAGQuery, RAGResponse

router = APIRouter(tags=["rag"], prefix="/rag")


@router.post("/query", response_model=RAGResponse)
def rag_query(
    req: RAGQuery,
    pipeline: PipelineDep,
    _: ApiKeyDep = None,
) -> RAGResponse:
    """Run the full RAG pipeline: retrieve → rerank → generate."""
    image = _load_image_from_field(req.query_image) if req.query_image else None
    out = pipeline.run(
        query_text=req.query_text,
        query_image=image,
        top_k=req.top_k,
        rerank=req.rerank,
        rerank_top_k=req.rerank_top_k,
        generate=req.generate,
        generate_style=req.generate_style,
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
    )
    return RAGResponse(
        retrieved=out["retrieved"],
        reranked=out["reranked"],
        summary=out["summary"],
        timings=out["timings"],
        providers=out["providers"],
    )
