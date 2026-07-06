"""Pydantic schemas shared across the API, CLI, and pipeline layers."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class Recipe(BaseModel):
    """A single recipe sample."""

    model_config = ConfigDict(extra="allow")

    id: str
    title: str = ""
    text: str = ""                # full markdown / plain text
    image_url: Optional[HttpUrl] = None
    image_path: Optional[str] = None  # local path or base64 data URL
    metadata: dict = Field(default_factory=dict)


class RecipeWithScore(BaseModel):
    """A recipe plus the retrieval/rerank score assigned to it."""

    recipe: Recipe
    score: float
    rank: int


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    providers: dict[str, str]
    vector_store: str
    dataset_size: int


class IngestRequest(BaseModel):
    source: Literal["sample", "hf", "local"] = "sample"
    limit: int | None = Field(default=None, ge=1, le=10_000)
    force: bool = False


class IngestResponse(BaseModel):
    ingested: int
    skipped: int
    duration_sec: float
    dataset_source: str


class RetrieveRequest(BaseModel):
    query_text: str | None = None
    query_image: str | None = None     # base64 data URL or http(s) URL
    top_k: int = Field(default=5, ge=1, le=200)


class RetrieveResponse(BaseModel):
    results: list[RecipeWithScore]
    query_kind: Literal["text", "image", "text+image"]
    elapsed_sec: float


class RerankRequest(BaseModel):
    query_text: str
    candidates: list[Recipe] = Field(default_factory=list, max_length=200)
    top_k: int = Field(default=5, ge=1, le=200)


class RerankResponse(BaseModel):
    results: list[RecipeWithScore]
    elapsed_sec: float


class GenerateRequest(BaseModel):
    query: str
    recipes: list[Recipe] = Field(default_factory=list, max_length=50)
    style: Literal["summary", "comparison", "recipe_card"] = "summary"
    max_new_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class GenerateResponse(BaseModel):
    text: str
    model: str
    elapsed_sec: float


class RAGQuery(BaseModel):
    """Full end-to-end RAG query."""

    query_text: str | None = None
    query_image: str | None = None
    top_k: int = Field(default=5, ge=1, le=100)
    rerank: bool = True
    rerank_top_k: int = Field(default=20, ge=1, le=100)
    generate: bool = True
    generate_style: Literal["summary", "comparison", "recipe_card"] = "summary"
    max_new_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class RAGResponse(BaseModel):
    """Full end-to-end RAG response."""

    retrieved: list[RecipeWithScore]
    reranked: list[RecipeWithScore] | None = None
    summary: str | None = None
    timings: dict[str, float]
    providers: dict[str, str]


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    error: str
    detail: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
