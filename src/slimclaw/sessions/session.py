"""Session model - dataclass representing a conversation session."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    """Represents a conversation session.

    Session key format: agent:<agent_id>:<channel>:<scope>:<identifier>[:thread:<thread_id>]

    Examples:
        - agent:default:cli:user:tush
        - agent:sales-bot:slack:user:U123456
        - agent:support:slack:group:C789:thread:T456
    """

    session_key: str
    agent_id: str
    channel: str
    scope: str  # 'user' or 'group'
    identifier: str
    thread_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    id: Optional[int] = None

    @classmethod
    def from_key(cls, session_key: str) -> "Session":
        """Parse session_key into components."""
        parts = session_key.split(":")

        if len(parts) < 5:
            raise ValueError(
                f"Invalid session_key format: {session_key}. "
                "Expected: agent:<agent_id>:<channel>:<scope>:<identifier>[:thread:<thread_id>]"
            )

        if parts[0] != "agent":
            raise ValueError(
                f"Session key must start with 'agent:', got: {session_key}"
            )

        agent_id = parts[1]
        channel = parts[2]
        scope = parts[3]
        identifier = parts[4]
        thread_id = None

        if len(parts) == 7 and parts[5] == "thread":
            thread_id = parts[6]
        elif len(parts) != 5:
            raise ValueError(
                f"Invalid session_key format: {session_key}. "
                "Expected: agent:<agent_id>:<channel>:<scope>:<identifier>[:thread:<thread_id>]"
            )

        if scope not in ("user", "group"):
            raise ValueError(f"Invalid scope '{scope}', must be 'user' or 'group'")

        return cls(
            session_key=session_key,
            agent_id=agent_id,
            channel=channel,
            scope=scope,
            identifier=identifier,
            thread_id=thread_id,
        )

    @staticmethod
    def build_key(
        agent_id: str,
        channel: str,
        scope: str,
        identifier: str,
        thread_id: Optional[str] = None,
    ) -> str:
        """Build a session key from components."""
        key = f"agent:{agent_id}:{channel}:{scope}:{identifier}"
        if thread_id:
            key += f":thread:{thread_id}"
        return key
