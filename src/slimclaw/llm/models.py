"""Model registry with predefined models per provider."""

import subprocess
from dataclasses import dataclass
from typing import Optional

from slimclaw.llm.types import Provider


@dataclass
class ModelInfo:
    """Information about an LLM model."""

    id: str  # Model ID used in API calls
    name: str  # Display name
    description: str
    context_window: Optional[int] = None


def get_local_ollama_models() -> list[ModelInfo]:
    """Query Ollama for locally installed models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []

        models = []
        lines = result.stdout.strip().split("\n")
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
            # Format: NAME ID SIZE MODIFIED
            parts = line.split()
            if parts:
                model_id = parts[0]
                models.append(
                    ModelInfo(
                        id=model_id,
                        name=model_id,
                        description="Installed locally",
                    )
                )
        return models
    except Exception:
        return []


# ─── Ollama Models ─────────────────────────────────────────────────────────────

OLLAMA_MODELS = [
    ModelInfo(
        id="qwen2.5:7b",
        name="Qwen 2.5 7B",
        description="Fast, capable general-purpose model",
        context_window=32768,
    ),
    ModelInfo(
        id="qwen2.5:14b",
        name="Qwen 2.5 14B",
        description="Larger Qwen model, better reasoning",
        context_window=32768,
    ),
    ModelInfo(
        id="qwen2.5:32b",
        name="Qwen 2.5 32B",
        description="Largest Qwen model, best quality",
        context_window=32768,
    ),
    ModelInfo(
        id="llama3.2:3b",
        name="Llama 3.2 3B",
        description="Lightweight, fast responses",
        context_window=128000,
    ),
    ModelInfo(
        id="llama3.1:8b",
        name="Llama 3.1 8B",
        description="Balanced speed and capability",
        context_window=128000,
    ),
    ModelInfo(
        id="llama3.1:70b",
        name="Llama 3.1 70B",
        description="High capability, requires more RAM",
        context_window=128000,
    ),
    ModelInfo(
        id="codellama:7b",
        name="Code Llama 7B",
        description="Optimized for code generation",
        context_window=16384,
    ),
    ModelInfo(
        id="mistral:7b",
        name="Mistral 7B",
        description="Efficient European model",
        context_window=32768,
    ),
    ModelInfo(
        id="deepseek-coder:6.7b",
        name="DeepSeek Coder 6.7B",
        description="Strong coding capabilities",
        context_window=16384,
    ),
]

# ─── OpenAI Models ─────────────────────────────────────────────────────────────

OPENAI_MODELS = [
    ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        description="Most capable, multimodal",
        context_window=128000,
    ),
    ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        description="Fast and affordable",
        context_window=128000,
    ),
    ModelInfo(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        description="Previous flagship model",
        context_window=128000,
    ),
    ModelInfo(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        description="Fast, cost-effective",
        context_window=16385,
    ),
    ModelInfo(
        id="o1",
        name="o1",
        description="Advanced reasoning model",
        context_window=200000,
    ),
    ModelInfo(
        id="o1-mini",
        name="o1 Mini",
        description="Fast reasoning model",
        context_window=128000,
    ),
]

# ─── Anthropic Models ──────────────────────────────────────────────────────────

ANTHROPIC_MODELS = [
    ModelInfo(
        id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        description="Latest balanced model",
        context_window=200000,
    ),
    ModelInfo(
        id="claude-opus-4-20250514",
        name="Claude Opus 4",
        description="Most capable Claude",
        context_window=200000,
    ),
    ModelInfo(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        description="Previous generation Sonnet",
        context_window=200000,
    ),
    ModelInfo(
        id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        description="Fast and efficient",
        context_window=200000,
    ),
    ModelInfo(
        id="claude-3-opus-20240229",
        name="Claude 3 Opus",
        description="Previous flagship",
        context_window=200000,
    ),
]

# ─── Registry ──────────────────────────────────────────────────────────────────

MODELS_BY_PROVIDER: dict[Provider, list[ModelInfo]] = {
    Provider.OLLAMA: OLLAMA_MODELS,
    Provider.OPENAI: OPENAI_MODELS,
    Provider.ANTHROPIC: ANTHROPIC_MODELS,
}


def get_models(provider: Provider) -> list[ModelInfo]:
    """Get available models for a provider."""
    if provider == Provider.OLLAMA:
        # For Ollama, return locally installed models
        local_models = get_local_ollama_models()
        if local_models:
            return local_models
        # Fallback to predefined list if ollama command fails
        return MODELS_BY_PROVIDER.get(provider, [])
    return MODELS_BY_PROVIDER.get(provider, [])


def get_model(provider: Provider, model_id: str) -> Optional[ModelInfo]:
    """Get a specific model by ID."""
    for model in get_models(provider):
        if model.id == model_id:
            return model
    return None


def get_default_model(provider: Provider) -> ModelInfo:
    """Get the default model for a provider (first in list)."""
    models = get_models(provider)
    if not models:
        raise ValueError(f"No models defined for provider: {provider}")
    return models[0]
