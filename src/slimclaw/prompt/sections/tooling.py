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
        "schedule_reminder": "Schedule a one-time reminder. 'when' accepts HH:MM (24h), H:MM AM/PM, or ISO datetime. 'message' is the notification text.",
        "list_reminders": "List all active reminders and scheduled tasks with their IDs.",
        "cancel_reminder": "Cancel a reminder by its job ID (shown in list_reminders output).",
        "spawn_agent": (
            "Delegate a complex subtask to a specialised subagent. "
            "Provide a self-contained task description and optionally an agent_type "
            "defined in ~/.slimclaw/AGENTS.md. Returns the subagent's final response."
        ),
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
    lines.append(
        "- When the user asks to set a reminder or schedule something → use schedule_reminder with the exact time."
    )
    lines.append(
        "- When a task is complex, benefits from specialisation, or you want to isolate work → use spawn_agent with a self-contained task description."
    )

    return "\n".join(lines)
