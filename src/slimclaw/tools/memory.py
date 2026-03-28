"""Memory tools - thin wrappers around memory module functions."""

from langchain_core.tools import StructuredTool

from slimclaw.memory import memory_get, memory_search, memory_write

# ─── Tool Exports ──────────────────────────────────────────────────────────────

memory_write_tool = StructuredTool.from_function(
    memory_write,
    name="memory_write",
    description="Save a note to persistent memory (MEMORY.md).",
)

memory_search_tool = StructuredTool.from_function(
    memory_search,
    name="memory_search",
    description="Search memory files and session history. Use semantic=True for natural language similarity search, or regex pattern by default. Returns matching lines with file:line references.",
)

memory_get_tool = StructuredTool.from_function(
    memory_get,
    name="memory_get",
    description="Read from memory files (~/.slimclaw/). Use path for file (default MEMORY.md) and line_range for specific lines (e.g. '1-50' or '10').",
)
