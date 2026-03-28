"""Embeddings - vector storage and retrieval for semantic search."""

from slimclaw.memory.embeddings.providers import get_embedding
from slimclaw.memory.embeddings.store import EmbeddingStore
from slimclaw.memory.embeddings.types import EmbeddingProvider, SearchResult
from slimclaw.memory.embeddings.utils import cosine_similarity

__all__ = [
    "EmbeddingProvider",
    "SearchResult",
    "get_embedding",
    "EmbeddingStore",
    "cosine_similarity",
]
