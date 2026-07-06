"""Dataset loader.

Three sources are supported:

* ``sample`` — load the 200-recipe JSON shipped in ``data/sample_recipes.json``
* ``hf``     — stream the full HuggingFace recipe dataset (10,096 samples)
* ``local``  — load a custom JSON file at ``settings.dataset_local_path``

The loader returns a list of :class:`Recipe` objects that the rest of the
pipeline consumes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import structlog
from tqdm.auto import tqdm

from multimodal_rag.config import Settings, get_settings
from multimodal_rag.exceptions import DatasetError
from multimodal_rag.schemas import Recipe

log = structlog.get_logger(__name__)

SAMPLE_PATH = Path(__file__).parent / "sample_recipes.json"


class DatasetLoader:
    """Load recipes from sample / HF / local sources."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.s = settings or get_settings()

    # ------------------------------------------------------------------
    def load(
        self,
        source: str | None = None,
        limit: int | None = None,
    ) -> list[Recipe]:
        """Return a list of recipes.

        Args:
            source: ``sample`` | ``hf`` | ``local``. Defaults to settings.
            limit: Cap the number returned. ``None`` means all.
        """
        source = source or self.s.dataset_source
        log.info("loading_dataset", source=source, limit=limit)
        if source == "sample":
            recipes = self._load_sample()
        elif source == "hf":
            recipes = list(self._stream_hf())
        elif source == "local":
            recipes = self._load_local(self.s.dataset_local_path)
        else:
            raise DatasetError(f"unknown dataset source: {source}")
        if limit is not None:
            recipes = recipes[:limit]
        log.info("dataset_loaded", count=len(recipes))
        return recipes

    # ------------------------------------------------------------------
    def stream(
        self,
        source: str | None = None,
        limit: int | None = None,
    ) -> Iterator[Recipe]:
        """Yield recipes one-by-one (memory-efficient for the 10k HF set)."""
        source = source or self.s.dataset_source
        n = 0
        if source == "sample":
            for r in self._load_sample():
                if limit is not None and n >= limit:
                    return
                yield r
                n += 1
        elif source == "hf":
            for r in self._stream_hf():
                if limit is not None and n >= limit:
                    return
                yield r
                n += 1
        elif source == "local":
            for r in self._load_local(self.s.dataset_local_path):
                if limit is not None and n >= limit:
                    return
                yield r
                n += 1
        else:
            raise DatasetError(f"unknown dataset source: {source}")

    # ------------------------------------------------------------------
    def _load_sample(self) -> list[Recipe]:
        if not SAMPLE_PATH.exists():
            raise DatasetError(
                f"sample dataset not found at {SAMPLE_PATH}; run "
                "`python scripts/build_sample_dataset.py` to regenerate it."
            )
        with SAMPLE_PATH.open() as f:
            raw = json.load(f)
        return [Recipe.model_validate(r) for r in raw]

    def _load_local(self, path: str) -> list[Recipe]:
        p = Path(path)
        if not p.exists():
            raise DatasetError(f"local dataset not found at {path}")
        with p.open() as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise DatasetError(f"expected a JSON list at {path}")
        return [Recipe.model_validate(r) for r in raw]

    def _stream_hf(self) -> Iterator[Recipe]:
        try:
            from datasets import load_dataset
        except ImportError as e:  # pragma: no cover
            raise DatasetError("datasets package not installed") from e
        try:
            ds = load_dataset(self.s.dataset_hf_id, split="train", streaming=True)
        except Exception as e:
            raise DatasetError(f"cannot load HF dataset {self.s.dataset_hf_id}: {e}") from e

        n = 0
        for row in tqdm(ds, desc="ingesting HF dataset"):
            recipe = Recipe(
                id=str(row.get("id", n)),
                title=str(row.get("title", "")),
                text=str(row.get("recipe_markdown") or row.get("text") or ""),
                image_path=row.get("image_path"),
                metadata={
                    k: v
                    for k, v in row.items()
                    if k not in {"image", "image_path"}
                },
            )
            yield recipe
            n += 1
            if self.s.dataset_sample_size and n >= self.s.dataset_sample_size:
                break


def build_dataset_loader(settings: Settings | None = None) -> DatasetLoader:
    return DatasetLoader(settings or get_settings())
