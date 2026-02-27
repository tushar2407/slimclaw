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
class LLMConfig:
    """LLM configuration with provider-specific fields."""

    provider: Provider
    model: str
    base_url: Optional[str] = None  # Only used by Ollama

    @classmethod
    def from_dict(cls, config: dict) -> "LLMConfig":
        """Create LLMConfig from config dictionary."""
        provider_str = config.get("provider", "ollama")
        return cls(
            provider=Provider(provider_str),
            model=config.get("model", "qwen2.5:7b"),
            base_url=config.get("base_url"),
        )
