"""Runner - orchestrates REPL loop, UI, sessions, and agent interaction."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner

from slimclaw.agent import AgentState, InvokeResult, SlimclawAgent, StreamEvent
from slimclaw.config import load_config, save_config, get_config_path

# ─── Paths ────────────────────────────────────────────────────────────────────


def _get_sessions_dir() -> Path:
    """Get the sessions directory path."""
    # Try data/sessions from cwd first
    sessions_dir = Path.cwd() / "data" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


# ─── Runner Class ─────────────────────────────────────────────────────────────


class Runner:
    """Orchestrates REPL loop, UI, sessions, and agent interaction."""

    def __init__(self):
        self.agent = SlimclawAgent()
        self.console = Console()
        self.session_id: Optional[str] = None
        self.session_file: Optional[Path] = None
        self.sessions_dir = _get_sessions_dir()

    def run(self) -> None:
        """Main REPL loop."""
        self._new_session()
        self._print_banner()

        while True:
            try:
                user_input = self.console.input("[bold green]you>[/bold green] ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not user_input:
                continue

            # Handle commands
            if self._handle_command(user_input):
                continue

            # Run agent with UI
            result = self._run_with_ui(self.agent.stream(user_input))

            # Handle shell confirmation loop
            while result.needs_confirmation:
                result = self._handle_confirmation(result)

            # Save turn if we got a response
            if result.response:
                self._save_turn("human", user_input)
                self._save_turn("assistant", result.response)

            self.console.print()

    def _print_banner(self) -> None:
        """Print welcome banner."""
        self.console.print(
            "[bold cyan]slimclaw[/bold cyan] — type [bold]/exit[/bold] to quit, "
            "[bold]/new[/bold] to reset session\n"
        )

    def _handle_command(self, user_input: str) -> bool:
        """
        Handle slash commands.

        Returns True if a command was handled (skip agent).
        """
        if user_input == "/exit":
            raise SystemExit(0)

        if user_input == "/new":
            self._new_session()
            self.console.print("[dim]Session reset.[/dim]\n")
            return True

        return False

    def _new_session(self) -> None:
        """Create a new session."""
        self.session_id = (
            datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        )
        self.session_file = self.sessions_dir / f"{self.session_id}.jsonl"
        self.agent.new_session(self.session_id)

    def _save_turn(self, role: str, content: str) -> None:
        """Save a conversation turn to the session file."""
        if self.session_file:
            with open(self.session_file, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "role": role,
                            "content": content,
                            "ts": datetime.now().isoformat(),
                        }
                    )
                    + "\n"
                )

    def _run_with_ui(
        self, events: Generator[StreamEvent, None, None]
    ) -> InvokeResult:
        """
        Consume stream events and update Rich UI.

        Returns the final InvokeResult.
        """
        result: Optional[InvokeResult] = None
        final_text = ""

        with Live(
            Spinner("dots", text=" thinking..."),
            console=self.console,
            refresh_per_second=10,
        ) as live:
            for event in events:
                if event.type == "tool_call":
                    # Show tool being called
                    tool = event.data
                    args_str = self._fmt_args(tool.tool_args)
                    self.console.print(
                        f"⚙  [cyan]{tool.tool_name}[/cyan]([dim]{args_str}[/dim])"
                    )
                    live.update(Spinner("dots", text=" running tool..."))

                elif event.type == "tool_result":
                    # Show tool result
                    tool_name = event.data["tool"]
                    content = event.data["result"]
                    preview = content[:200] + "..." if len(content) > 200 else content
                    self.console.print(f"✓  [green]{tool_name}[/green]")
                    if preview.strip():
                        self.console.print(f"   [dim]{preview}[/dim]")
                    live.update(Spinner("dots", text=" thinking..."))

                elif event.type == "text":
                    # Agent text response
                    final_text = event.data

                elif event.type == "interrupt":
                    # Needs confirmation - return immediately
                    live.update("")
                    return event.data

                elif event.type == "complete":
                    # Done - show final response
                    result = event.data
                    if result.response:
                        self.console.print(Markdown(result.response))

            live.update("")

        # If we didn't get a complete event, create a default result
        if result is None:
            result = InvokeResult(
                response=final_text or None,
                state=AgentState.COMPLETED,
                pending_tools=[],
            )

        return result

    def _handle_confirmation(self, result: InvokeResult) -> InvokeResult:
        """Prompt user for shell command approval."""
        # Show pending commands
        for tool in result.pending_tools:
            if tool.tool_name == "shell":
                command = tool.tool_args.get("command", "")
                self.console.print(f"[yellow]Shell command:[/yellow] {command}")

        # Get user choice
        self.console.print("[dim]Run this command? [y/n/always/never][/dim]")
        try:
            choice = self.console.input("[bold yellow]>[/bold yellow] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            choice = "n"

        if choice in ("y", "yes", "always"):
            if choice == "always":
                self._set_shell_preference(True)
                self.console.print("[dim]Preference saved — auto-run enabled.[/dim]")
            # Resume execution
            return self._run_with_ui(self.agent.resume())
        else:
            if choice == "never":
                self._set_shell_preference(False)
                self.console.print("[dim]Preference saved — shell execution disabled.[/dim]")
            # Cancel
            return self.agent.cancel()

    def _set_shell_preference(self, allow: bool) -> None:
        """Update shell auto_run preference in config."""
        config = load_config()
        config["shell"]["auto_run"] = allow
        save_config(config)

    def _fmt_args(self, args: dict) -> str:
        """Format tool arguments for display."""
        parts = []
        for k, v in args.items():
            v_str = str(v)
            if len(v_str) > 40:
                parts.append(f"{k}={v_str[:40]!r}...")
            else:
                parts.append(f"{k}={v_str!r}")
        return ", ".join(parts)
