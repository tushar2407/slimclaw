"""Memory tool - append notes to persistent memory."""

from datetime import datetime

from langchain_core.tools import StructuredTool
from .base import SLIMCLAW_DIR, MEMORY_FILE


def memory_write(note: str) -> str:
    """Append a note to MEMORY.md in ~/.slimclaw/."""
    SLIMCLAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n- [{timestamp}] {note}\n"
    with open(MEMORY_FILE, "a") as f:
        f.write(entry)
    return "Memory saved."


tool = StructuredTool.from_function(
    memory_write,
    name="memory",
    description="Save a note to persistent memory (MEMORY.md).",
)
