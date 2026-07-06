"""VectorStore protocol + shared data types."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy as np
from pydantic import BaseModel, Field

from multimodal_rag.schemas import Recipe


class VectorRecord(BaseModel):
    """A single record stored in the vector database."""

    id: str
    vector: list[float]
    payload: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_recipe(cls, recipe: Recipe, vector: np.ndarray | list[float]) -> "VectorRecord":
        """Build a record from a Recipe + its embedding vector."""
        if isinstance(vector, np.ndarray):
            vector = vector.astype(float).tolist()
        return cls(
            id=recipe.id,
            vector=vector,
            payload=recipe.model_dump(mode="json"),
        )


@runtime_checkable
class VectorStore(Protocol):
    """Persistence + similarity-search interface for embeddings."""

    name: str

    def upsert(self, records: list[VectorRecord]) -> int:
        """Insert (or replace) records. Returns the number written."""

    def search(
        self,
        query: np.ndarray,
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[tuple[Recipe, float]]:
        """Return ``(recipe, score)`` pairs ranked by similarity to ``query``."""

    def count(self) -> int:
        """Total records in the collection."""

    def delete_all(self) -> int:
        """Drop every record. Returns the number deleted."""

    def health(self) -> bool:
        """Return True if the store is reachable and ready."""
