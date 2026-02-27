import re
from pathlib import Path
from typing import List

from langchain_core.tools import StructuredTool

from slimclaw.tools.base import resolve_path


def grep(
    pattern: str,
    path: str = ".",
    before: int = 0,
    after: int = 0,
    ignore_case: bool = True,
    max_matches: int = 200,
) -> str:
    """Search for a regex pattern in files under a path.

    Args:
        pattern: Regular expression to search for.
        path: File or directory to search in (default ".").
        before: Number of context lines before each match (-B).
        after: Number of context lines after each match (-A).
        ignore_case: Case-insensitive search if True.
        max_matches: Maximum number of matches to return.

    Returns:
        Matching lines with optional context, similar to grep output.
    """
    if not pattern:
        return "Pattern must not be empty."

    base = resolve_path(path)
    if not base.exists():
        return f"Path not found: {path}"

    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Invalid regex pattern: {e}"

    files: List[Path] = []
    if base.is_file():
        files = [base]
    else:
        for p in base.rglob("*"):
            if p.is_file():
                files.append(p)

    lines_out: List[str] = []
    match_count = 0

    for file_path in files:
        try:
            lines = file_path.read_text(errors="ignore").splitlines()
        except Exception:
            continue

        for i, line in enumerate(lines):
            if not regex.search(line):
                continue

            start = max(0, i - before)
            end = min(len(lines) - 1, i + after)

            for j in range(start, end + 1):
                prefix = ":" if j == i else "-"
                lines_out.append(f"{file_path}:{j + 1}{prefix} {lines[j]}")

            lines_out.append("")
            match_count += 1
            if match_count >= max_matches:
                lines_out.append(f"... (truncated after {max_matches} matches)")
                return "\n".join(lines_out)

    if not lines_out:
        return f"No matches found for pattern: {pattern!r} in {path}"

    return "\n".join(lines_out)


tool = StructuredTool.from_function(
    grep,
    name="grep",
    description="Regex search in files with optional context lines (-A/-B). Path can be a file or directory.",
)

