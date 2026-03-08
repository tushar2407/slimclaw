"""Session manager - SQLite storage for sessions."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from slimclaw.sessions.session import Session
from slimclaw.sessions.utils import get_connection


class SessionManager:
    """Manages sessions in SQLite."""

    def __init__(self, db_path: Path):
        """Initialize SessionManager.

        Args:
            db_path: Path to database file.
        """
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

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
