"""Session management - Session model and SessionManager."""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

_SESSIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL UNIQUE,
    agent_id TEXT NOT NULL DEFAULT 'default',
    channel TEXT NOT NULL,
    scope TEXT NOT NULL,
    identifier TEXT NOT NULL,
    thread_id TEXT,
    started_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_channel ON sessions(channel);
CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions(last_active_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);
"""


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


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create a database connection with optimal settings."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Initialize database schema."""
    conn.executescript(_SESSIONS_SCHEMA)
    conn.commit()


class SessionManager:
    """Manages sessions in SQLite."""

    def __init__(self, db_path: Path):
        """Initialize SessionManager.

        Args:
            db_path: Path to database file.
        """
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        """Ensure database is initialized."""
        _init_schema(self._get_conn())

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create connection."""
        if self._conn is None:
            self._conn = get_connection(self._db_path)
        return self._conn

    @property
    def conn(self) -> sqlite3.Connection:
        """Get database connection."""
        return self._get_conn()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def get_or_create_session(
        self,
        session_key: str,
        metadata: Optional[dict] = None,
    ) -> Session:
        """Get existing session or create new one."""
        conn = self._get_conn()

        row = conn.execute(
            "SELECT * FROM sessions WHERE session_key = ?", (session_key,)
        ).fetchone()

        if row:
            now = datetime.now().isoformat()
            conn.execute(
                "UPDATE sessions SET last_active_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            conn.commit()
            return self._row_to_session(row)

        session = Session.from_key(session_key)
        session.metadata = metadata or {}
        return self._insert_session(session)

    def _insert_session(self, session: Session) -> Session:
        """Insert a new session."""
        conn = self._get_conn()
        now = datetime.now().isoformat()

        cursor = conn.execute(
            """
            INSERT INTO sessions
            (session_key, agent_id, channel, scope, identifier, thread_id, started_at, last_active_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.session_key,
                session.agent_id,
                session.channel,
                session.scope,
                session.identifier,
                session.thread_id,
                now,
                now,
                json.dumps(session.metadata),
            ),
        )
        conn.commit()
        session.id = cursor.lastrowid
        session.started_at = datetime.fromisoformat(now)
        session.last_active_at = session.started_at
        return session

    def get_session(self, session_key: str) -> Optional[Session]:
        """Get session by key, None if not found."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_key = ?", (session_key,)
        ).fetchone()
        return self._row_to_session(row) if row else None

    def list_sessions(
        self,
        channel: Optional[str] = None,
        limit: int = 50,
    ) -> list[Session]:
        """List sessions, optionally filtered by channel."""
        conn = self._get_conn()

        if channel:
            rows = conn.execute(
                """
                SELECT * FROM sessions
                WHERE channel = ?
                ORDER BY last_active_at DESC LIMIT ?
                """,
                (channel, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY last_active_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [self._row_to_session(row) for row in rows]

    def delete_session(self, session_key: str) -> bool:
        """Delete a session. Returns True if deleted."""
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM sessions WHERE session_key = ?", (session_key,)
        )
        conn.commit()
        return cursor.rowcount > 0

    def update_last_active(self, session_key: str) -> None:
        """Update last_active_at timestamp for a session."""
        conn = self._get_conn()
        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE sessions SET last_active_at = ? WHERE session_key = ?",
            (now, session_key),
        )
        conn.commit()

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert database row to Session object."""
        return Session(
            id=row["id"],
            session_key=row["session_key"],
            agent_id=row["agent_id"],
            channel=row["channel"],
            scope=row["scope"],
            identifier=row["identifier"],
            thread_id=row["thread_id"],
            started_at=datetime.fromisoformat(row["started_at"]),
            last_active_at=datetime.fromisoformat(row["last_active_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
