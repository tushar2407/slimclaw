"""Configuration - paths, defaults, and config file management."""

from pathlib import Path
from typing import Any

# ─── Paths ─────────────────────────────────────────────────────────────────────

SLIMCLAW_DIR = Path.home() / ".slimclaw"
DB_PATH = SLIMCLAW_DIR / "slimclaw.db"
CONFIG_FILE = SLIMCLAW_DIR / "config.json"
SESSIONS_DIR = SLIMCLAW_DIR / "sessions"  # JSONL message archives
MEMORY_DIR = SLIMCLAW_DIR / "memory"  # Consolidated memory files
MEMORY_FILE = SLIMCLAW_DIR / "MEMORY.md"  # User notes

# ─── Default Configuration ─────────────────────────────────────────────────────

DEFAULT_CONFIG: dict[str, Any] = {
    "llm": {
        "provider": "ollama",
        "model": "qwen2.5:7b",
        "base_url": "http://localhost:11434",
    },
    "shell": {
        "auto_run": None,
    },
    "embeddings": {
        "provider": "ollama",
        "model": "nomic-embed-text",
        "enabled": True,
        "consolidation_threshold": 10,
    },
}

DEFAULT_EMBEDDING_MODELS: dict[str, str] = {
    "ollama": "nomic-embed-text",
    "openai": "text-embedding-ada-002",
}
