import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from duckduckgo_search import DDGS

# Agent-specific files (SOUL.md, MEMORY.md) live in ~/.slimclaw/
SLIMCLAW_DIR = Path.home() / ".slimclaw"
MEMORY_FILE = SLIMCLAW_DIR / "MEMORY.md"


def read(path: str) -> str:
    """Read a file. Relative paths resolve from current working directory."""
    target = Path(path) if Path(path).is_absolute() else Path.cwd() / path
    if not target.exists():
        return f"File not found: {path}"
    return target.read_text()


def write(path: str, content: str) -> str:
    """Write content to a file. Relative paths resolve from current working directory."""
    target = Path(path) if Path(path).is_absolute() else Path.cwd() / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"Written: {target}"


def run_shell(command: str, confirmed: bool = False) -> str:
    """Run a shell command. Requires confirmation unless auto_run is set."""
    config_path = Path(__file__).parent / "config.json"
    config = json.loads(config_path.read_text())

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


def web_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    if not results:
        return "No results found."
    return "\n\n".join(
        f"{r['title']}\n{r['href']}\n{r['body']}" for r in results
    )


def memory_write(note: str) -> str:
    """Append a note to MEMORY.md in ~/.slimclaw/."""
    SLIMCLAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n- [{timestamp}] {note}\n"
    with open(MEMORY_FILE, "a") as f:
        f.write(entry)
    return "Memory saved."


# Tool definitions for LangChain
from langchain_core.tools import StructuredTool

TOOLS = [
    StructuredTool.from_function(
        read, name="read",
        description="Read a file. Relative paths resolve from the working directory."
    ),
    StructuredTool.from_function(
        write, name="write",
        description="Write content to a file. Relative paths resolve from the working directory."
    ),
    StructuredTool.from_function(
        run_shell, name="shell",
        description="Run a shell command. Use for: finding files (find, ls -la), exploring directories, running scripts, system commands."
    ),
    StructuredTool.from_function(
        web_search, name="web_search",
        description="Search the web using DuckDuckGo."
    ),
    StructuredTool.from_function(
        memory_write, name="memory",
        description="Save a note to persistent memory (MEMORY.md)."
    ),
]
