"""Configuration loading and management."""

import json
from pathlib import Path
from typing import Any

# Config lives in ~/.slimclaw/
SLIMCLAW_DIR = Path.home() / ".slimclaw"
CONFIG_FILE = SLIMCLAW_DIR / "config.json"

# Default configuration
DEFAULT_CONFIG: dict[str, Any] = {
    "llm": {
        "provider": "ollama",
        "model": "qwen2.5:7b",
        "base_url": "http://localhost:11434",
    },
    "shell": {
        "auto_run": None,
    },
}


def _ensure_config_dir() -> None:
    """Ensure ~/.slimclaw/ directory exists."""
    SLIMCLAW_DIR.mkdir(parents=True, exist_ok=True)


def _migrate_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate old config format to new format.

    Old format:
        {"ollama": {"model": "...", "base_url": "..."}, "shell": {...}}

    New format:
        {"llm": {"provider": "ollama", "model": "...", "base_url": "..."}, "shell": {...}}
    """
    if "llm" in config:
        # Already new format
        return config

    if "ollama" in config:
        # Migrate old format
        ollama_config = config.pop("ollama")
        config["llm"] = {
            "provider": "ollama",
            "model": ollama_config.get("model", "qwen2.5:7b"),
            "base_url": ollama_config.get("base_url", "http://localhost:11434"),
        }

    return config


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.slimclaw/config.json."""
    if CONFIG_FILE.exists():
        config = json.loads(CONFIG_FILE.read_text())
        return _migrate_config(config)

    # Return defaults if no config exists
    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to ~/.slimclaw/config.json."""
    _ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_config_path() -> Path:
    """Get the config file path."""
    return CONFIG_FILE
