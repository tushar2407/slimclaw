import json
import os
import platform
from datetime import datetime
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from tools import TOOLS
from langgraph.prebuilt import create_react_agent
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner

SLIMCLAW_DIR = Path.home() / ".slimclaw"
CONFIG_FILE = Path(__file__).parent / "config.json"
console = Console()


def _get_git_branch() -> str:
    """Get current git branch, or None if not in a git repo."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def build_env_context() -> dict:
    """Build a dictionary of environmental context for the agent."""
    import sys
    import socket

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


def load_config() -> dict:
    return json.loads(CONFIG_FILE.read_text())


def build_system_prompt(env: dict) -> str:
    """Build the system prompt with environmental context."""
    soul = (SLIMCLAW_DIR / "SOUL.md").read_text() if (SLIMCLAW_DIR / "SOUL.md").exists() else ""
    memory = (SLIMCLAW_DIR / "MEMORY.md").read_text() if (SLIMCLAW_DIR / "MEMORY.md").exists() else ""

    env_section = "\n".join(f"- {k}: {v}" for k, v in env.items())

    prompt = f"""You are a personal assistant running inside slimclaw.

## Environment
{env_section}

## Approach
Before telling the user something cannot be done:
1. Think carefully — can a tool help? Can you search for it, read it, or run a command?
2. Try the most logical tool first. If it fails, try another approach.
3. Only say you cannot do something after genuinely exhausting your options.

## Behaviour
- Actions speak louder than words. Just do it, don't announce it.
- Be concise. No filler phrases.
- If a task needs multiple steps, do them, then summarise the result.
- Memory is limited to this session unless you write to MEMORY.md.

## Tools
- `read`: Relative paths resolve from your working directory. Use absolute paths for files elsewhere.
- `write`: Creates/overwrites files. Relative paths resolve from working directory.
- `shell`: Use for discovering files (`find . -name "*.md"`), listing directories (`ls -la`), running commands.
- `memory`: Saves notes to ~/.slimclaw/MEMORY.md (persists across sessions).
- When a file isn't found, search for it with shell before giving up.
"""
    if soul.strip():
        prompt += f"\n## Persona\n{soul}"
    if memory.strip():
        prompt += f"\n## Memory\n{memory}"
    return prompt


def run_agent(user_input: str, chat_history: list) -> str:
    config = load_config()
    llm = ChatOllama(model=config["model"], base_url=config["ollama_base_url"])
    env = build_env_context()
    agent = create_react_agent(llm, TOOLS, prompt=build_system_prompt(env))

    messages = chat_history + [HumanMessage(content=user_input)]

    final_text = ""

    with Live(Spinner("dots", text=" thinking..."), console=console, refresh_per_second=10) as live:
        for event in agent.stream({"messages": messages}, stream_mode="updates"):
            for node, data in event.items():
                msgs = data.get("messages", [])
                for msg in msgs:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            console.print(f"⚙  [cyan]{tc['name']}[/cyan]([dim]{_fmt_args(tc['args'])}[/dim])")
                            live.update(Spinner("dots", text=" running tool..."))

                    elif hasattr(msg, "name") and msg.name:
                        # Tool result - show name and truncated content
                        content = getattr(msg, "content", "") or ""
                        preview = content[:200] + "..." if len(content) > 200 else content
                        console.print(f"✓  [green]{msg.name}[/green]")
                        if preview.strip():
                            console.print(f"   [dim]{preview}[/dim]")
                        live.update(Spinner("dots", text=" thinking..."))

                    elif hasattr(msg, "content") and msg.content and node == "agent":
                        final_text = msg.content
                        # live.update(Markdown(final_text))
                        console.print(Markdown(final_text))

        # Clear spinner before final output
        live.update("")

    if final_text == "NEEDS_CONFIRMATION":
        return "__SHELL_CONFIRM__"

    return final_text


def _fmt_args(args: dict) -> str:
    parts = []
    for k, v in args.items():
        v_str = str(v)
        parts.append(f"{k}={v_str[:40]!r}" if len(v_str) > 40 else f"{k}={v_str!r}")
    return ", ".join(parts)
