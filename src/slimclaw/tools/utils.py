"""Common utilities for tools."""

from pathlib import Path


def resolve_path(path: str) -> Path:
    """Resolve a path. Absolute paths used as-is, relative paths from cwd."""
    return Path(path) if Path(path).is_absolute() else Path.cwd() / path
