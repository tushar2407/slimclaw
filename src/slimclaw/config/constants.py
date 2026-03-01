from typing import Any

from slimclaw.constants import SLIMCLAW_DIR

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
