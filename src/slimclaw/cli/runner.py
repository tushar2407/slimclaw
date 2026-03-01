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
from slimclaw.config import load_config, save_config
from slimclaw.constants import SESSIONS_DIR
from slimclaw.llm import LLMConfigurationError, Provider, get_models


# ─── Runner Class ─────────────────────────────────────────────────────────────


class Runner:
    """Orchestrates REPL loop, UI, sessions, and agent interaction."""

    def __init__(self):
        self.agent = SlimclawAgent()
        self.console = Console()
        self.session_id: Optional[str] = None
        self.session_file: Optional[Path] = None
        self.sessions_dir = SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        """Main REPL loop."""
        self._new_session()
        self._print_banner()

        while True:
            try:
                user_input = self.console.input(
                    "[bold green]you>[/bold green] "
                ).strip()
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
        config = load_config()
        llm_config = config.get("llm", {})
        provider = llm_config.get("provider", "ollama")
        model = llm_config.get("model", "qwen2.5:7b")

        self.console.print(
            f"[bold cyan]slimclaw[/bold cyan] — using [green]{provider}[/green]/"
            f"[green]{model}[/green]\n"
            "  [bold]/exit[/bold] quit  [bold]/new[/bold] reset  "
            "[bold]/model[/bold] change model\n"
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

        if user_input == "/model":
            self._prompt_model_selection()
            return True

        return False

    def _prompt_model_selection(self) -> None:
        """Interactive model selection flow."""
        # Step 1: Select provider
        providers = list(Provider)
        self.console.print("\n[bold]Select provider:[/bold]")
        for i, p in enumerate(providers, 1):
            self.console.print(f"  {i}. {p.value}")

        try:
            choice = self.console.input("[bold yellow]>[/bold yellow] ").strip()
            if not choice:
                self.console.print("[dim]Cancelled.[/dim]\n")
                return
            provider_idx = int(choice) - 1
            if provider_idx < 0 or provider_idx >= len(providers):
                self.console.print("[red]Invalid choice.[/red]\n")
                return
            provider = providers[provider_idx]
        except (ValueError, KeyboardInterrupt, EOFError):
            self.console.print("[dim]Cancelled.[/dim]\n")
            return

        # Step 2: Select model
        models = get_models(provider)
        self.console.print(f"\n[bold]Select {provider.value} model:[/bold]")
        for i, m in enumerate(models, 1):
            self.console.print(f"  {i}. [cyan]{m.name}[/cyan] — {m.description}")

        try:
            choice = self.console.input("[bold yellow]>[/bold yellow] ").strip()
            if not choice:
                self.console.print("[dim]Cancelled.[/dim]\n")
                return
            model_idx = int(choice) - 1
            if model_idx < 0 or model_idx >= len(models):
                self.console.print("[red]Invalid choice.[/red]\n")
                return
            model = models[model_idx]
        except (ValueError, KeyboardInterrupt, EOFError):
            self.console.print("[dim]Cancelled.[/dim]\n")
            return

        # Step 3: Persist or session-only?
        self.console.print("\n[bold]Save to config?[/bold]")
        self.console.print("  1. Yes, persist for future sessions")
        self.console.print("  2. No, this session only")

        try:
            choice = self.console.input("[bold yellow]>[/bold yellow] ").strip()
            persist = choice == "1"
        except (KeyboardInterrupt, EOFError):
            persist = False

        # Apply selection
        config = load_config()
        config["llm"] = {
            "provider": provider.value,
            "model": model.id,
        }
        if provider == Provider.OLLAMA:
            config["llm"]["base_url"] = "http://localhost:11434"

        if persist:
            save_config(config)
            self.console.print(
                f"[green]Saved![/green] Using {provider.value}/{model.id}\n"
            )
        else:
            self.console.print(
                f"[green]Set for this session:[/green] {provider.value}/{model.id}\n"
            )

        # Reinitialize agent with new config
        try:
            self.agent = SlimclawAgent(config)
            self._new_session()
        except LLMConfigurationError as e:
            self.console.print(f"[red]Error:[/red] {e}\n")
            # Revert to previous agent
            self.agent = SlimclawAgent()
            self._new_session()

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

    def _run_with_ui(self, events: Generator[StreamEvent, None, None]) -> InvokeResult:
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
                self.console.print(
                    "[dim]Preference saved — shell execution disabled.[/dim]"
                )
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


def main():
    runner = Runner()
    runner.run()
