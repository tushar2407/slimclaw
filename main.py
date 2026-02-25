import json
import uuid
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage
from rich.console import Console
# from rich.markdown import Markdown

from agent import run_agent
from tools import memory_write_tool
from tools.shell import shell_instance

console = Console()
SESSIONS_DIR = Path(__file__).parent / "sessions"
CONFIG_FILE = Path(__file__).parent / "config.json"
SESSIONS_DIR.mkdir(exist_ok=True)


def save_turn(session_file: Path, role: str, content: str):
    with open(session_file, "a") as f:
        f.write(
            json.dumps(
                {"role": role, "content": content, "ts": datetime.now().isoformat()}
            )
            + "\n"
        )


def set_shell_preference(allow: bool):
    config = json.loads(CONFIG_FILE.read_text())
    config["shell"]["auto_run"] = allow
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    pref = "allow" if allow else "deny"
    memory_write_tool.run(f"User shell execution preference: {pref}")


def new_session():
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    return session_id, SESSIONS_DIR / f"{session_id}.jsonl", []


def main():
    console.print(
        "[bold cyan]slimclaw[/bold cyan] — type [bold]/exit[/bold] to quit, [bold]/new[/bold] to reset session\n"
    )

    session_id, session_file, chat_history = new_session()

    while True:
        try:
            user_input = console.input("[bold green]you>[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/new":
            session_id, session_file, chat_history = new_session()
            console.print("[dim]Session reset.[/dim]\n")
            continue

        # Normal chat flow: tools handle their own confirmations internally
        response = run_agent(user_input, chat_history)

        save_turn(session_file, "human", user_input)
        save_turn(session_file, "assistant", response)
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=response))

        # console.print(Markdown(response))
        console.print()


if __name__ == "__main__":
    main()
