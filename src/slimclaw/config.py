"""Configuration - paths, defaults, and config file management."""

import json
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


# ─── Config File Operations ────────────────────────────────────────────────────


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.slimclaw/config.json."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to ~/.slimclaw/config.json."""
    SLIMCLAW_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
