"""Embedding store - SQLite storage and search for embeddings."""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from slimclaw.config import DB_PATH
from slimclaw.memory.embeddings.types import SearchResult
from slimclaw.sessions.manager import get_connection


class EmbeddingStore:
    """Stores and searches embeddings in SQLite."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        conn: Optional[sqlite3.Connection] = None,
    ):
        """Initialize EmbeddingStore."""
        self._db_path = db_path or DB_PATH
        self._conn = conn

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create connection."""
        if self._conn is None:
            self._conn = get_connection(self._db_path)
        return self._conn

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def add_embedding(
        self,
        session_key: str,
        message_index: int,
        content: str,
        embedding: np.ndarray,
    ) -> None:
        """Store an embedding for a message."""
        conn = self._get_conn()
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        embedding_bytes = embedding.tobytes()
        now = datetime.now().isoformat()

        conn.execute(
            """
            INSERT OR REPLACE INTO embeddings
            (session_key, message_index, content_hash, embedding, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_key, message_index, content_hash, embedding_bytes, now),
        )
        conn.commit()

    def get_embedding(
        self, session_key: str, message_index: int
    ) -> Optional[np.ndarray]:
        """Get embedding for a specific message."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT embedding FROM embeddings WHERE session_key = ? AND message_index = ?",
            (session_key, message_index),
        ).fetchone()

        if row is None:
            return None
        return np.frombuffer(row[0], dtype=np.float32)

    def has_embedding(self, session_key: str, message_index: int) -> bool:
        """Check if embedding exists for a message."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM embeddings WHERE session_key = ? AND message_index = ?",
            (session_key, message_index),
        ).fetchone()
        return row is not None

    def get_last_embedded_index(self, session_key: str) -> int:
        """Get the highest message index that has been embedded."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT MAX(message_index) FROM embeddings WHERE session_key = ?",
            (session_key,),
        ).fetchone()
        return row[0] if row[0] is not None else -1

    def search(
        self,
        query_embedding: np.ndarray,
        session_key: Optional[str] = None,
        top_k: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SearchResult]:
        """Search for similar embeddings."""
        conn = self._get_conn()

        if session_key:
            rows = conn.execute(
                "SELECT session_key, message_index, content_hash, embedding FROM embeddings WHERE session_key = ?",
                (session_key,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT session_key, message_index, content_hash, embedding FROM embeddings"
            ).fetchall()

        if not rows:
            return []

        # Vectorized similarity computation
        embeddings = np.frombuffer(
            b"".join(row[3] for row in rows), dtype=np.float32
        ).reshape(len(rows), -1)

        row_norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        row_norms[row_norms == 0] = 1.0
        embeddings_norm = embeddings / row_norms

        query_norm = np.linalg.norm(query_embedding)
        query_normalized = (
            query_embedding / query_norm if query_norm > 0 else query_embedding
        )

        similarities = np.dot(embeddings_norm, query_normalized)

        results = []
        for i, similarity in enumerate(similarities):
            if similarity >= min_similarity:
                results.append(
                    SearchResult(
                        session_key=rows[i][0],
                        message_index=rows[i][1],
                        content_hash=rows[i][2],
                        similarity=float(similarity),
                    )
                )

        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:top_k]

    def delete_session_embeddings(self, session_key: str) -> int:
        """Delete all embeddings for a session."""
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM embeddings WHERE session_key = ?", (session_key,)
        )
        conn.commit()
        return cursor.rowcount

    def count_embeddings(self, session_key: Optional[str] = None) -> int:
        """Count embeddings, optionally for a specific session."""
        conn = self._get_conn()
        if session_key:
            row = conn.execute(
                "SELECT COUNT(*) FROM embeddings WHERE session_key = ?",
                (session_key,),
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
        return row[0]
