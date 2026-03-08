"""Sessions module - session management."""

from slimclaw.config import DB_PATH
from slimclaw.sessions.manager import Session, SessionManager, get_connection

# Default session manager instance
_default_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get the default SessionManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = SessionManager(DB_PATH)
    return _default_manager


__all__ = [
    "Session",
    "SessionManager",
    "get_connection",
    "get_session_manager",
]
