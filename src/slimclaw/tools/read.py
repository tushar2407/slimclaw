"""Read tool - read file contents."""

from langchain_core.tools import tool

from slimclaw.tools.utils import resolve_path


@tool
def read(path: str) -> str:
    """Read a file. Relative paths resolve from the working directory."""
    target = resolve_path(path)
    if not target.exists():
        return f"File not found: {path}"
    return target.read_text()
