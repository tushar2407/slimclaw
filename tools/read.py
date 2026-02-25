"""Read tool - read file contents."""

from langchain_core.tools import StructuredTool

from .base import resolve_path
from .types import err, ok


def read(path: str) -> str:
    """Read a file. Relative paths resolve from current working directory."""
    target = resolve_path(path)
    if not target.exists():
        return err(f"File not found: {path}", "not_found")
    try:
        return ok(target.read_text())
    except PermissionError:
        return err(f"Permission denied: {path}", "permission", recoverable=False)
    except Exception as e:
        return err(f"Read failed: {e}", "read_error")


tool = StructuredTool.from_function(
    read,
    name="read",
    description="Read a file. Relative paths resolve from the working directory.",
)
