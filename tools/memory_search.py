"""Memory search tool - grep-style search over memory files."""
import re
from pathlib import Path

from langchain_core.tools import StructuredTool
from .base import SLIMCLAW_DIR, MEMORY_FILE


def memory_search(query: str, case_insensitive: bool = True) -> str:
    """Search ~/.slimclaw/MEMORY.md and memory/*.md for a pattern.

    Returns matching lines with file path and line numbers.
    """
    results = []
    flags = re.IGNORECASE if case_insensitive else 0

    try:
        pattern = re.compile(query, flags)
    except re.error as e:
        return f"Invalid regex pattern: {e}"

    # Search MEMORY.md
    if MEMORY_FILE.exists():
        results.extend(_search_file(MEMORY_FILE, pattern))

    # Search memory/*.md files
    memory_dir = SLIMCLAW_DIR / "memory"
    if memory_dir.exists():
        for md_file in memory_dir.glob("*.md"):
            results.extend(_search_file(md_file, pattern))

    if not results:
        return f"No matches found for: {query}"

    return "\n".join(results[:50])  # Limit to 50 results


def _search_file(file_path: Path, pattern: re.Pattern) -> list[str]:
    """Search a single file and return matching lines."""
    matches = []
    try:
        lines = file_path.read_text().splitlines()
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                rel_path = file_path.relative_to(SLIMCLAW_DIR)
                matches.append(f"{rel_path}:{i}: {line.strip()}")
    except Exception:
        pass
    return matches


tool = StructuredTool.from_function(
    memory_search,
    name="memory_search",
    description="Search ~/.slimclaw/MEMORY.md and memory/*.md for a regex pattern. Returns matching lines with file:line references."
)
