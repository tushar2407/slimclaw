"""Shell tool - run shell commands."""

import json
import subprocess
from pathlib import Path

from langchain_core.tools import StructuredTool

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


class ShellTool:
    """Shell tool with encapsulated permission state."""

    def __init__(self):
        self._one_time_allow = False

    def allow_once(self):
        """Grant one-time permission (resets after use)."""
        self._one_time_allow = True

    def run(self, command: str) -> str:
        """Run a shell command. Requires user confirmation unless shell_auto_run is set in config."""
        config = json.loads(CONFIG_PATH.read_text())
        auto_run = config["shell"]["auto_run"]

        # Only allow if: config says always, or user just confirmed (one-time)
        allowed = auto_run is True or self._one_time_allow
        if self._one_time_allow:
            self._one_time_allow = False

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

    def as_tool(self) -> StructuredTool:
        """Return a LangChain StructuredTool bound to this instance."""
        return StructuredTool.from_function(
            self.run,
            name="shell",
            description="Run a shell command. Use for: finding files (find, ls -la), exploring directories, running scripts, system commands."
        )


# Module-level instance (single source of truth)
shell_instance = ShellTool()
tool = shell_instance.as_tool()
