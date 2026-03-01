"""Type definitions for LLM configuration."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Provider(str, Enum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class Model:
    """Unified model configuration and metadata."""

    id: str  # Model ID used in API calls (e.g. "gpt-4o", "qwen2.5:7b")
    provider: Provider
    name: str  # Display name
    description: str
    context_window: Optional[int] = None
    base_url: Optional[str] = None  # Only used by Ollama

    @classmethod
    def from_dict(cls, data: dict, provider: Provider) -> "Model":
        """Create Model from dictionary (JSON entry)."""
        return cls(
            id=data["id"],
            provider=provider,
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            context_window=data.get("context_window"),
            base_url=data.get("base_url"),
        )

    @classmethod
    def from_config(cls, config: dict) -> "Model":
        """Create Model from user config (selected model)."""
        provider_str = config.get("provider", "ollama")
        return cls(
            id=config.get("model", "qwen2.5:7b"),
            provider=Provider(provider_str),
            name=config.get("model", "qwen2.5:7b"),
            description="User selected",
            context_window=None,
            base_url=config.get("base_url"),
        )
