"""Write tool - create/overwrite files."""

from langchain_core.tools import StructuredTool

from slimclaw.tools.utils import resolve_path


def write(path: str, content: str) -> str:
    """Write content to a file. Relative paths resolve from current working directory."""
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"Written: {target}"


tool = StructuredTool.from_function(
    write,
    name="write",
    description="Write content to a file. Relative paths resolve from the working directory.",
)
