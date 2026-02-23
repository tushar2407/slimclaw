"""Common utilities for tools."""

from pathlib import Path

# Agent-specific files live in ~/.slimclaw/
SLIMCLAW_DIR = Path.home() / ".slimclaw"
MEMORY_FILE = SLIMCLAW_DIR / "MEMORY.md"


def resolve_path(path: str) -> Path:
    """Resolve a path. Absolute paths used as-is, relative paths from cwd."""
    return Path(path) if Path(path).is_absolute() else Path.cwd() / path
