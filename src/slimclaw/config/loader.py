"""Configuration loading and management."""

import json
from pathlib import Path
from typing import Any

from slimclaw.config.constants import DEFAULT_CONFIG, CONFIG_FILE, SLIMCLAW_DIR


def _ensure_config_dir() -> None:
    """Ensure ~/.slimclaw/ directory exists."""
    SLIMCLAW_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.slimclaw/config.json."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to ~/.slimclaw/config.json."""
    _ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_config_path() -> Path:
    """Get the config file path."""
    return CONFIG_FILE
