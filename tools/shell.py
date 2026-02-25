"""Shell tool - run shell commands."""

import json
import subprocess
from pathlib import Path

from langchain_core.tools import StructuredTool
from rich.console import Console

from .types import err, ok

CONFIG_PATH = Path(__file__).parent.parent / "config.json"
console = Console()


class ShellTool:
    """Shell tool with built-in, per-command confirmation."""

    def __init__(self):
        pass

    def _set_shell_preference(self, allow: bool) -> None:
        """Persist user preference for shell auto_run."""
        config = json.loads(CONFIG_PATH.read_text())
        config.setdefault("shell", {})
        config["shell"]["auto_run"] = allow
        CONFIG_PATH.write_text(json.dumps(config, indent=2))

    def _confirm_command(self, command: str) -> bool:
        """Ask the user whether to run this specific command."""
        cmd_preview = (
            command[:60] + "..." if len(command) > 60 else command
        ) or "(empty command)"

        while True:
            answer = (
                console.input(
                    f"[yellow]assistant>[/yellow] Run shell command [dim]`{cmd_preview}`[/dim]? [y/n/always/never]: "
                )
                .strip()
                .lower()
            )

            if answer in ("y", "yes"):
                return True
            if answer == "always":
                self._set_shell_preference(True)
                console.print("[dim]Preference saved — won't ask again.[/dim]")
                return True
            if answer in ("n", "no"):
                return False
            if answer == "never":
                self._set_shell_preference(False)
                console.print("[dim]Preference saved — shell execution disabled.[/dim]")
                return False
            # Anything else, re-prompt

    def run(self, command: str) -> str:
        """Run a shell command, asking the user for confirmation when needed."""
        config = json.loads(CONFIG_PATH.read_text())
        shell_cfg = config.get("shell", {})
        auto_run = shell_cfg.get("auto_run")

        # Respect persistent preference first
        if auto_run is True:
            allowed = True
        elif auto_run is False:
            return "DENIED: user has disabled auto shell execution."
        else:
            # No stored preference: ask just for this command
            allowed = self._confirm_command(command)

        if not allowed:
            return "Shell command cancelled."

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
