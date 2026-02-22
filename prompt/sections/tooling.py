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
        "memory_search": "Search memory files for a pattern. Returns file:line matches.",
        "memory_get": "Read specific lines from a memory file.",
    }

    for tool in tools:
        name = tool.name
        desc = tool_docs.get(name, tool.description)
        lines.append(f"- `{name}`: {desc}")

    # Usage guidance
    lines.append("")
    lines.append("### Guidance")
    lines.append("- When a file isn't found, search for it with shell before giving up.")
    lines.append("- Use memory_search then memory_get to recall past context.")

    return "\n".join(lines)
