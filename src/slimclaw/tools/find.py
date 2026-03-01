"""Search for files matching a glob pattern."""

from langchain_core.tools import StructuredTool

from slimclaw.tools.utils import resolve_path


def find(pattern: str, base_dir: str = ".") -> str:
    """Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g. \"*.py\", \"**/*.md\").
        base_dir: Base directory to search from (default \".\").

    Returns:
        List of matching paths, one per line, relative to the base directory.
    """
    if not pattern:
        return "Pattern must not be empty."

    base = resolve_path(base_dir)
    if not base.exists():
        return f"Base directory not found: {base_dir}"
    if not base.is_dir():
        return f"Base path is not a directory: {base_dir}"

    # Always return absolute paths so the agent can use results directly
    matches = sorted(p.resolve() for p in base.rglob(pattern))
    if not matches:
        return f"No files matched pattern {pattern!r} under {base_dir}"

    paths = [str(p) for p in matches]
    if len(paths) > 500:
        shown = paths[:500]
        return "\n".join(shown + [f"... ({len(paths) - 500} more not shown)"])

    return "\n".join(paths)


tool = StructuredTool.from_function(
    find,
    name="find",
    description="Glob pattern file search (e.g. '*.py', '**/*.md') under a base directory. Returns absolute paths.",
)
