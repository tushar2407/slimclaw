"""Memory tools - write, search, and get from persistent memory."""

import json
import re
from datetime import datetime
from pathlib import Path

from langchain_core.tools import StructuredTool
from .base import SLIMCLAW_DIR, MEMORY_FILE

# Sessions directory is relative to the project root
SESSIONS_DIR = Path(__file__).parent.parent / "sessions"


# ─── Memory Write ──────────────────────────────────────────────────────────────


def memory_write(note: str) -> str:
    """Append a note to MEMORY.md in ~/.slimclaw/."""
    SLIMCLAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n- [{timestamp}] {note}\n"
    with open(MEMORY_FILE, "a") as f:
        f.write(entry)
    return "Memory saved."


# ─── Memory Search ─────────────────────────────────────────────────────────────


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


# ─── Memory Get ────────────────────────────────────────────────────────────────


def memory_get(path: str = "MEMORY.md", line_range: str = "") -> str:
    """Read from a memory file, optionally a specific line range.

    Args:
        path: Path relative to ~/.slimclaw/ (e.g. "MEMORY.md" or "memory/notes.md").
              Default "MEMORY.md".
        line_range: Optional. Examples:
                    - "1-50" -> lines 1 through 50
                    - "10" -> just line 10
                    - "10,20,30" -> lines 10, 20, 30
                    - "" or omitted -> entire file

    Returns:
        File contents for the requested range, or an error message.
    """
    # Resolve path - must be under ~/.slimclaw/
    target = (SLIMCLAW_DIR / path).resolve()
    if not target.resolve().is_relative_to(SLIMCLAW_DIR.resolve()):
        return f"Path must be under ~/.slimclaw/: {path}"

    if not target.exists():
        return f"Memory file not found: {path}"

    try:
        lines = target.read_text().splitlines()
    except Exception as e:
        return f"Could not read file: {e}"

    total = len(lines)
    if total == 0:
        return f"File is empty: {path}"

    if not line_range or not line_range.strip():
        return "\n".join(lines)

    # Parse line_range: "1-50" or "10" or "10,20,30"
    indices: set[int] = set()
    for part in re.split(r"[,;]\s*", line_range.strip()):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                start, end = int(a.strip()), int(b.strip())
                for i in range(max(1, start), min(total, end) + 1):
                    indices.add(i)
            except ValueError:
                continue
        else:
            try:
                i = int(part)
                if 1 <= i <= total:
                    indices.add(i)
            except ValueError:
                continue

    if not indices:
        return f"Invalid line range: {line_range}. File has {total} lines."

    result_lines = [lines[i - 1] for i in sorted(indices)]
    return "\n".join(result_lines)


# ─── Tool Exports ──────────────────────────────────────────────────────────────

memory_write_tool = StructuredTool.from_function(
    memory_write,
    name="memory_write",
    description="Save a note to persistent memory (MEMORY.md).",
)

memory_search_tool = StructuredTool.from_function(
    memory_search,
    name="memory_search",
    description="Search memory files and session history for a regex pattern. Returns matching lines with file:line references.",
)

memory_get_tool = StructuredTool.from_function(
    memory_get,
    name="memory_get",
    description="Read from memory files (~/.slimclaw/). Use path for file (default MEMORY.md) and line_range for specific lines (e.g. '1-50' or '10').",
)
