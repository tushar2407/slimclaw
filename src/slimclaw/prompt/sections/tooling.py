"""Tooling section - available tools and usage guidance."""


def build_tooling_section(tools: list) -> str:
    """Build the tooling section with tool descriptions."""
    if not tools:
        return ""

    lines = ["## Tools"]

    # Tool descriptions
    tool_docs = {
        "read": "Read a file. Relative paths resolve from working directory.",
        "write": "Write/create a file. Relative paths resolve from working directory.",
        "shell": "Run shell commands. Use for: find, ls, git, etc.",
        "web_search": "Search the web via DuckDuckGo.",
        "memory": "Save a note to persistent memory (~/.slimclaw/MEMORY.md).",
        "memory_search": "Search memory files AND session history for a pattern. Returns matches with context.",
        "memory_get": "Read specific lines/sections from memory files (~/.slimclaw/). Use line_range e.g. '1-50' or '10'.",
        "edit": "String replacement in files (old_string → new_string). Path can be a file path or glob pattern.",
        "grep": "Regex search in files with optional context lines (-A/-B/-C).",
        "find": "Glob pattern file search (e.g. '*.py', '**/*.md') under a base directory.",
        "ls": "Directory listing. Names only by default; use long=True for details (mode, size, mtime).",
    }

    for tool in tools:
        name = tool.name
        desc = tool_docs.get(name, tool.description)
        lines.append(f"- `{name}`: {desc}")

    # Usage guidance
    lines.append("")
    lines.append("### Guidance")
    lines.append(
        "- When a file isn't found, search for it with shell before giving up."
    )
    lines.append(
        "- When the user asks you to remember something → always call the memory tool to save it."
    )
    lines.append(
        "- When the user asks what you remember → call memory_search or memory_get to read from MEMORY.md (do not rely on session context)."
    )

    return "\n".join(lines)
