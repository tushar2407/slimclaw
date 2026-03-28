"""Message archiving - JSONL storage for conversation history."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from slimclaw.config import DB_PATH, SESSIONS_DIR
from slimclaw.sessions import SessionManager


class MessageArchive:
    """Manages JSONL message archives."""

    def __init__(self, sessions_dir: Optional[Path] = None):
        """Initialize MessageArchive.

        Args:
            sessions_dir: Directory for JSONL archives. Defaults to SESSIONS_DIR.
        """
        self._sessions_dir = sessions_dir or SESSIONS_DIR
        self._message_counts: dict[str, int] = {}
        self._session_mgr = SessionManager(DB_PATH)

    def get_archive_path(self, session_key: str) -> Path:
        """Get JSONL archive path for a session.

        Sanitizes session_key: 'agent:default:cli:user:tush' → 'agent_default_cli_user_tush.jsonl'
        """
        safe_name = session_key.replace(":", "_").replace("/", "_")
        return self._sessions_dir / f"{safe_name}.jsonl"

    def archive_message(
        self,
        session_key: str,
        role: str,
        content: str,
        tool_name: Optional[str] = None,
        tool_args: Optional[dict] = None,
    ) -> int:
        """Append message to JSONL archive.

        Args:
            session_key: Session key to archive message for
            role: Message role ('human', 'assistant', 'system', 'tool')
            content: Message content
            tool_name: Optional tool name for tool messages
            tool_args: Optional tool arguments dict

        Returns:
            The index of the newly archived message (0-based)
        """
        archive_path = self.get_archive_path(session_key)
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        current_count = self.get_message_count(session_key)
        now = datetime.now().isoformat()

        # Update session last_active_at
        self._session_mgr.update_last_active(session_key)

        # Append to JSONL archive
        with open(archive_path, "a") as f:
            f.write(
                json.dumps(
                    {
                        "role": role,
                        "content": content,
                        "ts": now,
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                    }
                )
                + "\n"
            )

        self._message_counts[session_key] = current_count + 1
        return current_count

    def get_message_count(self, session_key: str) -> int:
        """Get the number of messages in a session's archive."""
        if session_key in self._message_counts:
            return self._message_counts[session_key]

        archive_path = self.get_archive_path(session_key)
        if not archive_path.exists():
            count = 0
        else:
            with open(archive_path) as f:
                count = sum(1 for _ in f)

        self._message_counts[session_key] = count
        return count

    def get_messages(
        self,
        session_key: str,
        start_index: int = 0,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Get messages from archive starting at index.

        Args:
            session_key: Session key
            start_index: Line number to start from (0-indexed)
            limit: Maximum messages to return, None for all

        Returns:
            List of message dicts
        """
        archive_path = self.get_archive_path(session_key)
        if not archive_path.exists():
            return []

        messages = []
        with open(archive_path) as f:
            for i, line in enumerate(f):
                if i < start_index:
                    continue
                if limit and len(messages) >= limit:
                    break
                try:
                    messages.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        return messages
