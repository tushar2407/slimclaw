"""Subagent data types - context, result, and agent definition dataclasses."""

import queue
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from slimclaw.agent.types import StreamEvent


@dataclass
class SubAgentContext:
    """Passed into spawn_agent tool at creation time. Carries depth + event channel."""

    parent_session_key: str
    depth: int
    event_queue: "queue.Queue[StreamEvent]"
    max_depth: int = 2


@dataclass
class SubAgentResult:
    success: bool
    response: str
    error: Optional[str] = None


@dataclass
class AgentDefinition:
    name: str
    description: str
    tools: list[str]  # tool names, or ["all"]
    model: str = "inherit"  # "inherit" or "provider/model_id"
