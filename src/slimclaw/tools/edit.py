"""Replace all occurrences of old string with new string in the given file or files."""

from pathlib import Path
from typing import List

from langchain_core.tools import tool

from slimclaw.tools.utils import resolve_path


@tool
def edit(path: str, old_string: str, new_string: str) -> str:
    """Replace all occurrences of old_string with new_string in a file or glob pattern.

    Args:
        path: File path or glob pattern. Relative paths resolve from current working directory.
        old_string: Exact text to search for.
        new_string: Replacement text.

    Returns:
        Summary of modified files and replacement counts.
    """
    if not old_string:
        return "old_string must not be empty."

    paths: List[Path] = []

    if any(ch in path for ch in "*?[]"):
        paths = sorted(Path.cwd().rglob(path))
    else:
        target = resolve_path(path)
        if target.is_dir():
            return "Path is a directory; please provide a file path or glob pattern."
        if not target.exists():
            return f"File not found: {path}"
        paths = [target]

    if not paths:
        return f"No files matched pattern: {path}"

    results = []
    total_replacements = 0

    for file_path in paths:
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text()
        except Exception:
            continue

        count = text.count(old_string)
        if count == 0:
            continue

        new_text = text.replace(old_string, new_string)
        try:
            file_path.write_text(new_text)
        except Exception:
            continue

        total_replacements += count
        results.append(f"{file_path}: {count} replacements")

    if not results:
        return f"No occurrences of {old_string!r} found in matched files."

    header = f"Total replacements: {total_replacements} in {len(results)} file(s)"
    return "\n".join([header] + results)
