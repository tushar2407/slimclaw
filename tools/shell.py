"""Shell tool - run shell commands."""

import json
import subprocess
from pathlib import Path

from langchain_core.tools import StructuredTool

from .types import err, ok

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


class ShellTool:
    """Shell tool with encapsulated permission state."""

    def __init__(self):
        self._turn_allow = False

    def allow_turn(self):
        """Grant permission for the current agent turn (until revoke() is called)."""
        self._turn_allow = True

    def revoke(self):
        """Revoke turn permission (call after agent turn completes)."""
        self._turn_allow = False

    def run(self, command: str) -> str:
        """Run a shell command. Requires user confirmation unless shell_auto_run is set in config."""
        config = json.loads(CONFIG_PATH.read_text())
        auto_run = config["shell"]["auto_run"]

        # Allow if: config says always, or user confirmed for this turn
        allowed = auto_run is True or self._turn_allow

        if not allowed:
            if auto_run is False:
                return "DENIED: user has disabled auto shell execution."
            return "NEEDS_CONFIRMATION"

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or result.stderr
            return ok(output.strip() or "(no output)")
        except subprocess.TimeoutExpired:
            return err("Command timed out after 30s", "timeout")
        except Exception as e:
            return err(str(e), "shell_error")

    def as_tool(self) -> StructuredTool:
        """Return a LangChain StructuredTool bound to this instance."""
        return StructuredTool.from_function(
            self.run,
            name="shell",
            description="Run a shell command. Use for: finding files (find, ls -la), exploring directories, running scripts, system commands.",
        )


# Module-level instance (single source of truth)
shell_instance = ShellTool()
tool = shell_instance.as_tool()
