"""Memory get tool - read specific lines/sections from memory files."""

import re

from langchain_core.tools import StructuredTool
from .base import SLIMCLAW_DIR


def memory_get(path: str = "MEMORY.md", line_range: str = "") -> str:
    """Read from a memory file, optionally a specific line range.

    Args:
        path: Path relative to ~/.slimclaw/ (e.g. "MEMORY.md" or "memory/notes.md").
              Default "MEMORY.md".
        line_range: Optional. Examples:
                    - "1-50" → lines 1 through 50
                    - "10" → just line 10
                    - "10,20,30" → lines 10, 20, 30
                    - "" or omitted → entire file

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


tool = StructuredTool.from_function(
    memory_get,
    name="memory_get",
    description="Read from memory files (~/.slimclaw/). Use path for file (default MEMORY.md) and line_range for specific lines (e.g. '1-50' or '10').",
)
