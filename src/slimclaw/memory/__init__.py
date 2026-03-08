"""Memory module - archiving, embeddings, consolidation, and search."""

from slimclaw.memory.archive import MessageArchive, get_archive
from slimclaw.memory.consolidator import MemoryConsolidator, extract_memories
from slimclaw.memory.embeddings import (
    EmbeddingProvider,
    EmbeddingStore,
    SearchResult,
    get_embedding,
)
from slimclaw.memory.search import memory_get, memory_search, memory_write

__all__ = [
    # Archive
    "MessageArchive",
    "get_archive",
    # Embeddings
    "EmbeddingProvider",
    "EmbeddingStore",
    "SearchResult",
    "get_embedding",
    # Consolidation
    "MemoryConsolidator",
    "extract_memories",
    # Search
    "memory_search",
    "memory_write",
    "memory_get",
]
