import json
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from tools import TOOLS
from langgraph.prebuilt import create_react_agent
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner

WORKSPACE = Path(__file__).parent / "workspace"
CONFIG_FILE = Path(__file__).parent / "config.json"
console = Console()


def load_config() -> dict:
    return json.loads(CONFIG_FILE.read_text())


def build_system_prompt() -> str:
    soul = (WORKSPACE / "SOUL.md").read_text() if (WORKSPACE / "SOUL.md").exists() else ""
    memory = (WORKSPACE / "MEMORY.md").read_text() if (WORKSPACE / "MEMORY.md").exists() else ""

    prompt = """You are a personal assistant running inside slimclaw.

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
"""
    if soul.strip():
        prompt += f"\n## Persona\n{soul}"
    if memory.strip():
        prompt += f"\n## Memory\n{memory}"
    return prompt


def run_agent(user_input: str, chat_history: list) -> str:
    config = load_config()
    llm = ChatOllama(model=config["model"], base_url=config["ollama_base_url"])
    agent = create_react_agent(llm, TOOLS, prompt=build_system_prompt())

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
                        console.print(f"✓  [green]{msg.name}[/green]")
                        live.update(Spinner("dots", text=" thinking..."))

                    elif hasattr(msg, "content") and msg.content and node == "agent":
                        final_text = msg.content
                        live.update(Markdown(final_text))

    if final_text == "NEEDS_CONFIRMATION":
        return "__SHELL_CONFIRM__"

    return final_text


def _fmt_args(args: dict) -> str:
    parts = []
    for k, v in args.items():
        v_str = str(v)
        parts.append(f"{k}={v_str[:40]!r}" if len(v_str) > 40 else f"{k}={v_str!r}")
    return ", ".join(parts)
