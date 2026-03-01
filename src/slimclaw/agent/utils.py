from datetime import datetime
from pathlib import Path
import os
import platform
import socket
import subprocess
import sys
from typing import Optional


def _get_git_branch() -> Optional[str]:
    """Get current git branch, or None if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def build_env_context() -> dict:
    """Build a dictionary of environmental context for the agent."""
    ctx = {
        "cwd": os.getcwd(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S %A"),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "hostname": socket.gethostname(),
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "home": str(Path.home()),
        "shell": os.environ.get("SHELL", "unknown"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    git_branch = _get_git_branch()
    if git_branch:
        ctx["git_branch"] = git_branch

    return ctx
