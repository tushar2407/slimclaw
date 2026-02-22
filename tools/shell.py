"""Shell tool - run shell commands."""
import json
import subprocess
from pathlib import Path

from langchain_core.tools import StructuredTool

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def run_shell(command: str, confirmed: bool = False) -> str:
    """Run a shell command. Requires confirmation unless auto_run is set."""
    config = json.loads(CONFIG_PATH.read_text())
    auto_run = config.get("shell_auto_run")

    if auto_run is None and not confirmed:
        return "NEEDS_CONFIRMATION"

    if auto_run is False and not confirmed:
        return "DENIED: user has disabled auto shell execution."

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
    description="Run a shell command. Use for: finding files (find, ls -la), exploring directories, running scripts, system commands."
)
