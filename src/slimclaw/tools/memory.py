"""Memory tools - thin wrappers around memory module functions."""

from langchain_core.tools import tool

from slimclaw.memory import (
    memory_get as _memory_get,
    memory_search as _memory_search,
    memory_write as _memory_write,
)


@tool
def memory_write(note: str) -> str:
    """Save a note to persistent memory (MEMORY.md)."""
    return _memory_write(note)


@tool
def memory_search(query: str, semantic: bool = False) -> str:
    """Search memory files and session history. Use semantic=True for natural language similarity search, or regex pattern by default. Returns matching lines with file:line references."""
    return _memory_search(query, semantic=semantic)


@tool
def memory_get(path: str = "MEMORY.md", line_range: str = "") -> str:
    """Read from memory files (~/.slimclaw/). Use path for file (default MEMORY.md) and line_range for specific lines (e.g. '1-50' or '10')."""
    return _memory_get(path, line_range=line_range)
