"""Shell tool - run shell commands."""

import json
import subprocess
from pathlib import Path

from langchain_core.tools import StructuredTool

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

# One-time allow: set by main.py when user says "y" to confirm
_allow_next_shell = False


def allow_next_shell(allow: bool = True):
    """Allow the next shell call (user confirmed). Used by main.py."""
    global _allow_next_shell
    _allow_next_shell = allow


def run_shell(command: str) -> str:
    """Run a shell command. Requires user confirmation unless shell_auto_run is set in config."""
    global _allow_next_shell
    config = json.loads(CONFIG_PATH.read_text())
    auto_run = config["shell"]["auto_run"]

    # Only allow if: config says always, or user just confirmed (one-time)
    allowed = auto_run is True or _allow_next_shell
    if _allow_next_shell:
        _allow_next_shell = False

    if not allowed:
        if auto_run is False:
            return "DENIED: user has disabled auto shell execution."
        return "NEEDS_CONFIRMATION"

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout or result.stderr
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30s"
    except Exception as e:
        return f"Error: {e}"


tool = StructuredTool.from_function(
    run_shell,
    name="shell",
    description="Run a shell command. Use for: finding files (find, ls -la), exploring directories, running scripts, system commands.",
)
