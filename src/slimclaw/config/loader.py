"""Configuration loading and management."""

import json
from pathlib import Path
from typing import Any

# Config file is at project root (two levels up from this file when installed)
# But we use a flexible approach to find it
_CONFIG_PATHS = [
    Path.cwd() / "config.json",  # Current working directory
    Path(__file__).parent.parent.parent.parent.parent / "config.json",  # Project root
]


def get_config_path() -> Path:
    """Find the config file path."""
    for path in _CONFIG_PATHS:
        if path.exists():
            return path
    # Default to cwd
    return Path.cwd() / "config.json"


def load_config() -> dict[str, Any]:
    """Load configuration from config.json."""
    config_path = get_config_path()
    if config_path.exists():
        return json.loads(config_path.read_text())
    # Return defaults if no config exists
    return {
        "ollama": {
            "model": "qwen2.5:7b",
            "base_url": "http://localhost:11434",
        },
        "shell": {
            "auto_run": None,
        },
    }


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to config.json."""
    config_path = get_config_path()
    config_path.write_text(json.dumps(config, indent=2))
