"""Memory search tool - grep-style search over memory and session files."""

import json
import re
from pathlib import Path

from langchain_core.tools import StructuredTool
from .base import SLIMCLAW_DIR, MEMORY_FILE

# Sessions directory is relative to the project root
SESSIONS_DIR = Path(__file__).parent.parent / "sessions"


def memory_search(query: str, case_insensitive: bool = True) -> str:
    """Search memory files and session history for a pattern.

    Searches:
    - ~/.slimclaw/MEMORY.md
    - ~/.slimclaw/memory/*.md
    - sessions/*.jsonl (conversation history)

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
        results.extend(_search_file(MEMORY_FILE, pattern, SLIMCLAW_DIR))

    # Search memory/*.md files
    memory_dir = SLIMCLAW_DIR / "memory"
    if memory_dir.exists():
        for md_file in memory_dir.glob("*.md"):
            results.extend(_search_file(md_file, pattern, SLIMCLAW_DIR))

    # Search session files
    if SESSIONS_DIR.exists():
        results.extend(_search_sessions(pattern))

    if not results:
        return f"No matches found for: {query}"

    return "\n".join(results[:50])  # Limit to 50 results


def _search_file(file_path: Path, pattern: re.Pattern, base_dir: Path) -> list[str]:
    """Search a single file and return matching lines."""
    matches = []
    try:
        lines = file_path.read_text().splitlines()
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                rel_path = file_path.relative_to(base_dir)
                matches.append(f"{rel_path}:{i}: {line.strip()}")
    except Exception:
        pass
    return matches


def _search_sessions(pattern: re.Pattern) -> list[str]:
    """Search through session JSONL files."""
    matches = []
    try:
        for jsonl_file in sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True):
            for line_num, line in enumerate(jsonl_file.read_text().splitlines(), 1):
                try:
                    entry = json.loads(line)
                    content = entry.get("content", "")
                    if pattern.search(content):
                        role = entry.get("role", "?")
                        preview = content[:300].replace("\n", " ")
                        if len(content) > 300:
                            preview += "..."
                        matches.append(
                            f"sessions/{jsonl_file.name}:{line_num}: [{role}] {preview}"
                        )
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return matches


tool = StructuredTool.from_function(
    memory_search,
    name="memory_search",
    description="Search memory files and session history for a regex pattern. Returns matching lines with file:line references.",
)
