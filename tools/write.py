"""Write tool - create/overwrite files."""

from langchain_core.tools import StructuredTool

from .base import resolve_path
from .types import err, ok


def write(path: str, content: str) -> str:
    """Write content to a file. Relative paths resolve from current working directory."""
    target = resolve_path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return ok(f"Written: {target}")
    except PermissionError:
        return err(f"Permission denied: {path}", "permission", recoverable=False)
    except Exception as e:
        return err(f"Write failed: {e}", "write_error")


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing all occurrences of old_string with new_string."""
    target = resolve_path(path)
    if not target.exists():
        return err(f"File not found: {path}", "not_found")
    try:
        content = target.read_text()
        if old_string not in content:
            return err(f"String not found in file: {old_string[:50]}", "not_found")
        content = content.replace(old_string, new_string)
        target.write_text(content)
        return ok(f"Edited: {target}")
    except PermissionError:
        return err(f"Permission denied: {path}", "permission", recoverable=False)
    except Exception as e:
        return err(f"Edit failed: {e}", "write_error")


tool = StructuredTool.from_function(
    write,
    name="write",
    description="Write content to a file. Relative paths resolve from the working directory.",
)
