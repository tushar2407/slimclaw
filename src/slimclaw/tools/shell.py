"""Shell tool - run shell commands.

Note: Approval is handled at the agent layer via interrupt_before=["tools"].
This tool just executes commands when called.
"""

import subprocess

from langchain_core.tools import tool


@tool
def shell(command: str) -> str:
    """Run a shell command. Use for: finding files (find, ls -la), exploring directories, running scripts, system commands."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout or result.stderr
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR [timeout]: Command timed out after 30s"
    except Exception as e:
        return f"ERROR [shell_error]: {e}"
