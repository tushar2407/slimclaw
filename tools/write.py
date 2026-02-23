"""Write tool - create/overwrite files."""

from langchain_core.tools import StructuredTool
from .base import resolve_path


def write(path: str, content: str) -> str:
    """Write content to a file. Relative paths resolve from current working directory."""
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"Written: {target}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing all occurrences of old_string with new_string."""
    target = resolve_path(path)
    content = target.read_text()
    content = content.replace(old_string, new_string)
    target.write_text(content)
    return f"Edited: {target}"


tool = StructuredTool.from_function(
    write,
    name="write",
    description="Write content to a file. Relative paths resolve from the working directory.",
)
