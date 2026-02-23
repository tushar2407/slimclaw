"""Type definitions for prompt building."""
from dataclasses import dataclass


@dataclass
class PromptContext:
    """Context passed to prompt section builders."""
    env: dict                    # Environment info (cwd, datetime, platform, etc.)
    tools: list                  # List of tool objects
    soul: str = ""               # SOUL.md content
    memory: str = ""             # MEMORY.md content
    cwd: str = ""                # Current working directory
