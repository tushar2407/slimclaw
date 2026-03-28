import json
from typing import Any

from slimclaw.config.constants import CONFIG_FILE, DEFAULT_CONFIG, SLIMCLAW_DIR


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.slimclaw/config.json."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to ~/.slimclaw/config.json."""
    SLIMCLAW_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
