"""Memory get tool - read specific sections from memory files."""
from pathlib import Path

from langchain_core.tools import StructuredTool
from .base import SLIMCLAW_DIR


def memory_get(file: str = "MEMORY.md", start_line: int = 1, num_lines: int = 50) -> str:
    """Read lines from a memory file in ~/.slimclaw/.

    Args:
        file: Filename relative to ~/.slimclaw/ (e.g., "MEMORY.md" or "memory/notes.md")
        start_line: Line number to start from (1-indexed)
        num_lines: Number of lines to read (default 50)

    Returns:
        The requested lines with line numbers.
    """
    file_path = SLIMCLAW_DIR / file

    if not file_path.exists():
        return f"File not found: {file}"

    # Security check - ensure path is within SLIMCLAW_DIR
    try:
        file_path.resolve().relative_to(SLIMCLAW_DIR.resolve())
    except ValueError:
        return f"Access denied: {file} is outside ~/.slimclaw/"

    try:
        lines = file_path.read_text().splitlines()
        total_lines = len(lines)

        # Adjust indices (1-indexed to 0-indexed)
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, start_idx + num_lines)

        if start_idx >= total_lines:
            return f"Start line {start_line} exceeds file length ({total_lines} lines)"

        selected = lines[start_idx:end_idx]
        result = [f"{i}: {line}" for i, line in enumerate(selected, start=start_line)]

        header = f"# {file} (lines {start_line}-{end_idx} of {total_lines})\n"
        return header + "\n".join(result)

    except Exception as e:
        return f"Error reading {file}: {e}"


tool = StructuredTool.from_function(
    memory_get,
    name="memory_get",
    description="Read specific lines from a memory file in ~/.slimclaw/. Use after memory_search to read context around matches."
)
