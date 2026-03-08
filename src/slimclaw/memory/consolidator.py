"""Memory consolidation - extracts facts, summaries, and action items from conversations."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from slimclaw.config import DB_PATH, MEMORY_DIR
from slimclaw.memory.archive import get_archive
from slimclaw.sessions.manager import get_connection

# ─── Extraction Prompts ────────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are a memory extraction assistant. Analyze conversations and extract key information.

Output your extraction in this exact markdown format:

### Facts
- Bullet points of concrete information (names, preferences, decisions, technical details)
- Only include facts that would be useful to remember in future conversations
- Skip trivial or obvious information

### Summary
A 1-2 sentence summary of the conversation topic and outcome.

### Action Items
- [ ] Any pending tasks, follow-ups, or commitments mentioned
- Leave empty if none

If there are no meaningful facts, summary, or action items to extract, output:

### Facts
- No significant facts extracted

### Summary
Brief conversation without notable outcomes.

### Action Items
(none)
"""

EXTRACTION_USER_TEMPLATE = """Extract memories from this conversation:

{messages}

Remember to use the exact markdown format specified."""


def extract_memories(messages: list[dict], llm: BaseChatModel) -> str:
    """Use LLM to extract structured memories from messages."""
    formatted_messages = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "human":
            formatted_messages.append(f"User: {content}")
        elif role == "assistant":
            formatted_messages.append(f"Assistant: {content}")
        elif role == "tool":
            tool_name = msg.get("tool_name", "unknown")
            formatted_messages.append(f"[Tool: {tool_name}] {content[:200]}...")

    messages_text = "\n\n".join(formatted_messages)

    response = llm.invoke(
        [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(
                content=EXTRACTION_USER_TEMPLATE.format(messages=messages_text)
            ),
        ]
    )

    return response.content


# ─── Consolidation State Schema ────────────────────────────────────────────────

_CONSOLIDATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS consolidation_state (
    session_key TEXT PRIMARY KEY,
    last_processed_index INTEGER DEFAULT 0,
    last_consolidated_at TEXT
);
"""


# ─── Memory Consolidator ───────────────────────────────────────────────────────


class MemoryConsolidator:
    """Manages memory consolidation - extracts facts/summaries from conversations."""

    def __init__(
        self,
        llm: BaseChatModel,
        db_path: Optional[Path] = None,
        consolidation_threshold: int = 10,
    ):
        """Initialize MemoryConsolidator.

        Args:
            llm: LangChain chat model for extraction
            db_path: Optional path to database file. Defaults to DB_PATH.
            consolidation_threshold: Number of new messages before consolidation
        """
        self._llm = llm
        self._db_path = db_path or DB_PATH
        self._threshold = consolidation_threshold
        self._conn: Optional[sqlite3.Connection] = None
        self._archive = get_archive()
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create connection."""
        if self._conn is None:
            self._conn = get_connection(self._db_path)
        return self._conn

    def _ensure_schema(self) -> None:
        """Ensure consolidation_state table exists."""
        conn = self._get_conn()
        conn.executescript(_CONSOLIDATION_SCHEMA)
        conn.commit()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def should_consolidate(self, session_key: str) -> bool:
        """Check if enough new messages since last consolidation."""
        last_processed = self._get_last_processed_index(session_key)
        current_count = self._archive.get_message_count(session_key)
        return (current_count - last_processed) >= self._threshold

    def consolidate(self, session_key: str) -> Optional[str]:
        """Run memory consolidation for a session.

        Extracts facts/summaries from new messages and appends to daily memory file.

        Returns:
            Path to memory file if consolidation ran, None if nothing to consolidate
        """
        last_processed = self._get_last_processed_index(session_key)
        messages = self._archive.get_messages(session_key, start_index=last_processed)

        if not messages:
            return None

        # Extract memories using LLM
        extraction = extract_memories(messages, self._llm)

        # Write to daily memory file
        memory_path = self._get_memory_path()
        self._append_to_memory_file(memory_path, session_key, extraction)

        # Update consolidation state
        new_index = last_processed + len(messages)
        self._update_consolidation_state(session_key, new_index)

        return str(memory_path)

    def _get_last_processed_index(self, session_key: str) -> int:
        """Get the last processed message index for a session."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT last_processed_index FROM consolidation_state WHERE session_key = ?",
            (session_key,),
        ).fetchone()
        return row[0] if row else 0

    def _update_consolidation_state(self, session_key: str, index: int) -> None:
        """Update the consolidation state for a session."""
        conn = self._get_conn()
        now = datetime.now().isoformat()
        conn.execute(
            """
            INSERT OR REPLACE INTO consolidation_state
            (session_key, last_processed_index, last_consolidated_at)
            VALUES (?, ?, ?)
            """,
            (session_key, index, now),
        )
        conn.commit()

    def _get_memory_path(self) -> Path:
        """Get path to today's memory file."""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        return MEMORY_DIR / f"{today}.md"

    def _append_to_memory_file(
        self, path: Path, session_key: str, extraction: str
    ) -> None:
        """Append extraction to memory file with session header."""
        now = datetime.now().strftime("%H:%M")
        header = f"\n## Session: {session_key} ({now})\n\n"

        if not path.exists():
            date_str = datetime.now().strftime("%Y-%m-%d")
            with open(path, "w") as f:
                f.write(f"# Memory Log - {date_str}\n")

        with open(path, "a") as f:
            f.write(header)
            f.write(extraction)
            f.write("\n")
