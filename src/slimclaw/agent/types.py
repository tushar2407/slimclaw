"""Type definitions for agent execution."""

from dataclasses import dataclass
from typing import Any, Optional

from slimclaw.agent.state import AgentState


@dataclass
class PendingToolCall:
    """Represents a tool call awaiting approval."""

    tool_name: str
    tool_args: dict
    tool_call_id: str


@dataclass
class InvokeResult:
    """Result from agent execution."""

    response: Optional[str]  # Final text response (None if interrupted)
    state: AgentState
    pending_tools: list[PendingToolCall]

    @property
    def needs_confirmation(self) -> bool:
        """Check if shell commands are pending approval."""
        return self.state == AgentState.INTERRUPTED and any(
            t.tool_name == "shell" for t in self.pending_tools
        )


@dataclass
class StreamEvent:
    """Events yielded during streaming execution."""

    type: str  # "tool_call", "tool_result", "text", "interrupt", "complete"
    data: Any  # Tool info, result content, text chunk, or InvokeResult
