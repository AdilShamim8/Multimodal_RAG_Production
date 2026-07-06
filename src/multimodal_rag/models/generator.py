"""Generator protocol + provider implementations.

The generator takes the user query + retrieved context and produces a
natural-language summary. The original notebook uses Qwen3-VL-2B-Instruct.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from multimodal_rag.config import Settings, get_settings
from multimodal_rag.exceptions import (
    GeneratorProviderError,
    ProviderNotAvailableError,
)
from multimodal_rag.monitoring import GENERATION_OPS
from multimodal_rag.schemas import Recipe

log = structlog.get_logger(__name__)


@runtime_checkable
class Generator(Protocol):
    """Produce a natural-language summary given a query and recipes."""

    name: str
    model_id: str

    def generate(
        self,
        query: str,
        recipes: list[Recipe],
        *,
        style: str = "summary",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """Return the generated text."""


# ---------------------------------------------------------------------------
# Prompt builder (shared across providers)
# ---------------------------------------------------------------------------


def build_prompt(query: str, recipes: list[Recipe], style: str) -> str:
    """Build the user-facing prompt handed to the generator."""
    recipe_lines = []
    for i, r in enumerate(recipes, start=1):
        recipe_lines.append(
            f"[{i}] {r.title}\n{r.text[:800]}"
        )
    recipes_block = "\n\n".join(recipe_lines) or "(no recipes retrieved)"

    if style == "comparison":
        instruction = (
            "Compare the following recipes. Highlight differences in "
            "ingredients, technique, and serving size. Be concise."
        )
    elif style == "recipe_card":
        instruction = (
            "Format the most relevant recipe below as a clean recipe card "
            "with: Title, Ingredients, Steps, Serving Size."
        )
    else:  # summary
        instruction = (
            "Summarise the following recipes for the user. Highlight 2–3 "
            "key ingredients, the cooking technique, and any tips."
        )

    return (
        f"You are a helpful culinary assistant. {instruction}\n\n"
        f"User query: {query}\n\n"
        f"Retrieved recipes:\n{recipes_block}\n\n"
        f"Assistant:"
    )


# ---------------------------------------------------------------------------
# Mock generator
# ---------------------------------------------------------------------------


class MockGenerator:
    """Deterministic template generator — no external deps, runs anywhere."""

    def __init__(self) -> None:
        self.name = "mock"
        self.model_id = "mock-generator"

    def generate(
        self,
        query: str,
        recipes: list[Recipe],
        *,
        style: str = "summary",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        GENERATION_OPS.labels(provider="mock").inc()
        if not recipes:
            return f"No recipes found for: {query}"
        titles = ", ".join(r.title for r in recipes[:5])
        return (
            f"[mock summary for '{query}'] "
            f"Found {len(recipes)} recipe(s): {titles}. "
            f"Top pick: {recipes[0].title}. "
            f"(Style: {style}; this is a deterministic mock generator — "
            f"set GENERATOR_PROVIDER=local_hf or openai for real generation.)"
        )


# ---------------------------------------------------------------------------
# Local HF generator (Qwen3-VL-2B-Instruct)
# ---------------------------------------------------------------------------


class LocalHFGenerator:
    """Qwen3-VL-2B-Instruct via transformers."""

    def __init__(
        self,
        model_id: str,
        device: str = "auto",
        torch_dtype: str = "auto",
    ) -> None:
        try:
            import torch  # noqa: F401
            from transformers import AutoModelForCausalLM, AutoProcessor
        except ImportError as e:  # pragma: no cover
            raise ProviderNotAvailableError(
                "local_hf generator requires the 'gpu' extra"
            ) from e
        import torch

        self.model_id = model_id
        self.name = "local_hf"
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        dtype_map = {
            "auto": torch.float16 if self.device.type == "cuda" else torch.float32,
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        self.dtype = dtype_map[torch_dtype]

        log.info(
            "loading_generator",
            model_id=model_id,
            device=str(self.device),
            dtype=str(self.dtype),
        )
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=self.dtype,
            trust_remote_code=True,
        ).to(self.device)
        self.model.eval()

    @retry(
        retry=retry_if_exception_type(GeneratorProviderError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )
    def generate(
        self,
        query: str,
        recipes: list[Recipe],
        *,
        style: str = "summary",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        import torch

        GENERATION_OPS.labels(provider="local_hf").inc()
        prompt = build_prompt(query, recipes, style)
        try:
            inputs = self.processor(
                text=prompt, return_tensors="pt", truncation=True, max_length=4096
            ).to(self.device)
            with torch.no_grad():
                out = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=temperature > 0,
                    temperature=max(temperature, 1e-3),
                    pad_token_id=getattr(self.processor, "eos_token_id", None),
                )
            text = self.processor.batch_decode(
                out[:, inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            )[0]
            return text.strip()
        except Exception as e:
            raise GeneratorProviderError(f"local_hf generate failed: {e}") from e


# ---------------------------------------------------------------------------
# OpenAI generator
# ---------------------------------------------------------------------------


class OpenAIGenerator:
    """OpenAI chat completions generator."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise ProviderNotAvailableError("openai generator requires OPENAI_API_KEY")
        try:
            import openai
        except ImportError as e:  # pragma: no cover
            raise ProviderNotAvailableError("pip install openai") from e
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.name = "openai"
        self.model_id = model

    @retry(
        retry=retry_if_exception_type(GeneratorProviderError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )
    def generate(
        self,
        query: str,
        recipes: list[Recipe],
        *,
        style: str = "summary",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        GENERATION_OPS.labels(provider="openai").inc()
        prompt = build_prompt(query, recipes, style)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful culinary assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_new_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise GeneratorProviderError(f"openai generate failed: {e}") from e


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_generator(settings: Settings | None = None) -> Generator:
    s = settings or get_settings()
    name = s.generator_provider
    log.info("building_generator", provider=name)
    if name == "mock":
        return MockGenerator()
    if name == "local_hf":
        return LocalHFGenerator(
            model_id=s.generator_model_id,
            device=s.model_device,
            torch_dtype=s.model_torch_dtype,
        )
    if name == "openai":
        return OpenAIGenerator(api_key=s.openai_api_key, model=s.openai_generator_model)
    raise ProviderNotAvailableError(f"unknown generator provider: {name}")


__all__ = [
    "Generator",
    "MockGenerator",
    "LocalHFGenerator",
    "OpenAIGenerator",
    "build_generator",
    "build_prompt",
]

_ = Any  # keep import in scope for type hints
