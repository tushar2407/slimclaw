"""Embedding types - provider enum and result dataclass."""

from dataclasses import dataclass
from enum import Enum


class EmbeddingProvider(Enum):
    """Supported embedding providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"


@dataclass
class SearchResult:
    """Result from embedding search."""

    session_key: str
    message_index: int
    content_hash: str
    similarity: float
