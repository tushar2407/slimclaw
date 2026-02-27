"""Workspace section - working directory info."""


def build_workspace_section(cwd: str) -> str:
    """Build the workspace section."""
    if not cwd:
        return ""

    return f"""## Workspace
Your working directory is: {cwd}
- File operations (read, write) resolve relative paths from here.
- Use absolute paths for files outside this directory."""
