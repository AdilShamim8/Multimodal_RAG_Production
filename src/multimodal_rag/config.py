"""Centralised application configuration.

All settings are read from environment variables (or a ``.env`` file) and
validated by pydantic-settings. A single :func:`get_settings` call returns a
cached :class:`Settings` instance — call ``get_settings.cache_clear()`` if you
need to reload after changing env vars at runtime.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Provider name aliases (kept as Literals so mypy can enforce them)
# ---------------------------------------------------------------------------
ProviderName = Literal["mock", "local_hf", "openai"]
VectorStoreName = Literal["chroma", "qdrant", "faiss"]
EnvName = Literal["dev", "staging", "prod"]


class Settings(BaseSettings):
    """Application settings.

    Every field has a default that lets the app start in CPU-only / mock mode
    with no external services. Flip the ``*_PROVIDER`` env vars to ``local_hf``
    or ``openai`` to enable real models.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App --------------------------------------------------------------
    app_name: str = "multimodal-rag"
    app_env: EnvName = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"
    app_workers: int = 1

    # --- Providers --------------------------------------------------------
    embedding_provider: ProviderName = "mock"
    reranker_provider: ProviderName = "mock"
    generator_provider: ProviderName = "mock"

    # HuggingFace model IDs
    embedding_model_id: str = "nvidia/Nemotron-Embed-VL"
    reranker_model_id: str = "nvidia/Llama-Nemotron-Rerank-VL"
    generator_model_id: str = "Qwen/Qwen3-VL-2B-Instruct"

    model_device: str = "auto"               # auto | cpu | cuda | mps
    model_torch_dtype: str = "auto"          # auto | float32 | float16 | bfloat16

    # OpenAI
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-large"
    openai_reranker_model: str = "gpt-4o-mini"
    openai_generator_model: str = "gpt-4o-mini"

    hf_token: str = ""

    # --- Vector store -----------------------------------------------------
    vector_store: VectorStoreName = "chroma"
    chroma_persist_dir: str = "./data/chroma"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "recipes"
    faiss_index_path: str = "./data/faiss/index.faiss"

    # --- Dataset ----------------------------------------------------------
    dataset_source: Literal["sample", "hf", "local"] = "sample"
    dataset_hf_id: str = "mrdbourke/recipe-synthetic-images-10k"
    dataset_local_path: str = "./data/sample_recipes.json"
    dataset_sample_size: int = 200
    dataset_images_dir: str = "./data/images"

    # --- Embeddings cache -------------------------------------------------
    embeddings_cache_path: str = "./data/embeddings.safetensors"
    embeddings_dim: int = 2048
    embedding_batch_size: int = 16

    # --- RAG pipeline -----------------------------------------------------
    default_top_k: int = 5
    rerank_top_k: int = 20
    generate_max_new_tokens: int = 512
    generate_temperature: float = 0.7

    # --- Reliability ------------------------------------------------------
    embedding_timeout_sec: int = 30
    embedding_max_retries: int = 3
    rate_limit_per_minute: int = 60

    # --- Cache ------------------------------------------------------------
    cache_enabled: bool = True
    cache_max_size: int = 1024

    # --- Monitoring -------------------------------------------------------
    enable_metrics: bool = True
    prometheus_multiproc_dir: str = "./data/prometheus"

    # --- Security ---------------------------------------------------------
    api_key: str = ""
    cors_origins: str = "*"

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    @field_validator("app_log_level")
    @classmethod
    def _normalise_log_level(cls, v: str) -> str:
        return v.upper()

    @field_validator("cors_origins")
    @classmethod
    def _strip_cors(cls, v: str) -> str:
        return v.strip() or "*"

    # ------------------------------------------------------------------
    # Convenience views
    # ------------------------------------------------------------------
    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"

    def ensure_dirs(self) -> None:
        """Create the on-disk directories the app relies on."""
        for p in [
            self.chroma_persist_dir,
            self.dataset_images_dir,
            Path(self.embeddings_cache_path).parent,
            Path(self.faiss_index_path).parent,
            self.prometheus_multiproc_dir,
        ]:
            Path(p).mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance."""
    s = Settings()  # type: ignore[call-arg]
    s.ensure_dirs()
    return s
