"""Model utility functions"""

import json
import subprocess
from pathlib import Path
from typing import Optional

from slimclaw.llm.types import Model, Provider


def _load_models() -> dict[Provider, list[Model]]:
    """Load models from JSON file."""
    _MODELS_BY_PROVIDER: dict[Provider, list[Model]] = {}
    _MODELS_FILE = Path(__file__).parent / "models.json"

    if not _MODELS_FILE.exists():
        return {}

    data = json.loads(_MODELS_FILE.read_text())

    for provider_str, models_list in data.items():
        try:
            provider = Provider(provider_str)
            _MODELS_BY_PROVIDER[provider] = [
                Model.from_dict(model_info, provider) for model_info in models_list
            ]
        except ValueError:
            # Unknown provider, skip
            continue

    return _MODELS_BY_PROVIDER


def get_local_ollama_models() -> list[Model]:
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
                    Model(
                        id=model_id,
                        provider=Provider.OLLAMA,
                        name=model_id,
                        description="Installed locally",
                    )
                )
        return models
    except Exception:
        return []


def get_models(provider: Provider) -> list[Model]:
    """Get available models for a provider."""
    models_by_provider = _load_models()

    if provider == Provider.OLLAMA:
        # For Ollama, return locally installed models
        local_models = get_local_ollama_models()
        if local_models:
            return local_models
        # Fallback to predefined list if ollama command fails
        return models_by_provider.get(provider, [])

    return models_by_provider.get(provider, [])


def get_model(provider: Provider, model_id: str) -> Optional[Model]:
    """Get a specific model by ID."""
    for model in get_models(provider):
        if model.id == model_id:
            return model
    return None


def get_default_model(provider: Provider) -> Model:
    """Get the default model for a provider (first in list)."""
    models = get_models(provider)
    if not models:
        raise ValueError(f"No models defined for provider: {provider}")
    return models[0]
