"""Agent execution states."""

from enum import Enum


class AgentState(Enum):
    """Agent execution states."""

    READY = "ready"
    INTERRUPTED = "interrupted"  # Awaiting tool approval
    COMPLETED = "completed"
