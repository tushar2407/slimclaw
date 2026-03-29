"""Write tool - create/overwrite files."""

from langchain_core.tools import tool

from slimclaw.tools.utils import resolve_path


@tool
def write(path: str, content: str) -> str:
    """Write content to a file. Relative paths resolve from the working directory."""
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"Written: {target}"
