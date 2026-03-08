"""Runner - orchestrates REPL loop, UI, sessions, and agent interaction."""

import os
from typing import Generator, Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner

from slimclaw.agent import AgentState, InvokeResult, SlimclawAgent, StreamEvent
from slimclaw.config import DB_PATH, load_config, save_config
from slimclaw.llm import LLMConfigurationError, Provider, get_models
from slimclaw.memory import get_archive
from slimclaw.sessions import Session, SessionManager

# Optional embeddings support
try:
    from slimclaw.memory import (
        EmbeddingProvider,
        EmbeddingStore,
        MemoryConsolidator,
        get_embedding,
    )

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


# ─── Runner Class ─────────────────────────────────────────────────────────────


class Runner:
    """Orchestrates REPL loop, UI, sessions, and agent interaction."""

    def __init__(self):
        self.agent = SlimclawAgent()
        self.console = Console()
        self.db = SessionManager(DB_PATH)
        self._archive = get_archive()
        self.session: Optional[Session] = None
        self._cli_user = os.environ.get("USER", os.environ.get("USERNAME", "default"))
        self._embedding_store: Optional["EmbeddingStore"] = None
        self._consolidator: Optional["MemoryConsolidator"] = None
        self._embeddings_enabled = False
        self._init_embeddings()

    def run(self) -> None:
        """Main REPL loop."""
        try:
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
        finally:
            self.db.close()

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

    def _init_embeddings(self) -> None:
        """Initialize embeddings and consolidation if available and enabled."""
        if not EMBEDDINGS_AVAILABLE:
            return

        config = load_config()
        embeddings_config = config.get("embeddings", {})

        if not embeddings_config.get("enabled", True):
            return

        try:
            self._embedding_store = EmbeddingStore()
            # Consolidator needs an LLM - create one from config
            from slimclaw.llm import create_llm
            from slimclaw.llm.types import Model, Provider as LLMProvider

            llm_config = config.get("llm", {})
            provider = LLMProvider(llm_config.get("provider", "ollama"))
            model = Model(
                id=llm_config.get("model", "qwen2.5:7b"),
                name=llm_config.get("model", "qwen2.5:7b"),
                provider=provider,
                description="",
                base_url=llm_config.get("base_url"),
            )
            llm = create_llm(model)

            threshold = embeddings_config.get("consolidation_threshold", 10)
            self._consolidator = MemoryConsolidator(
                llm=llm,
                consolidation_threshold=threshold,
            )
            self._embeddings_enabled = True
        except Exception:
            # Silently disable embeddings if initialization fails
            self._embeddings_enabled = False

    def _new_session(self) -> None:
        """Create or resume CLI session."""
        session_key = Session.build_key(
            agent_id="default",
            channel="cli",
            scope="user",
            identifier=self._cli_user,
        )
        self.session = self.db.get_or_create_session(session_key)
        self.agent.new_session(self.session.session_key)

    def _save_turn(self, role: str, content: str) -> None:
        """Save a conversation turn to the JSONL archive."""
        if not self.session:
            return

        session_key = self.session.session_key

        # Archive message and get its index
        msg_index = self._archive.archive_message(
            session_key=session_key,
            role=role,
            content=content,
        )

        # Generate and store embedding if enabled
        if self._embeddings_enabled and self._embedding_store:
            try:
                config = load_config()
                embeddings_config = config.get("embeddings", {})
                provider_name = embeddings_config.get("provider", "ollama")
                provider = EmbeddingProvider(provider_name)
                model = embeddings_config.get("model")

                embedding = get_embedding(content, provider=provider, model=model)
                self._embedding_store.add_embedding(
                    session_key=session_key,
                    message_index=msg_index,
                    content=content,
                    embedding=embedding,
                )
            except Exception:
                pass  # Silently skip embedding on error

        # Check for memory consolidation
        if self._embeddings_enabled and self._consolidator:
            try:
                if self._consolidator.should_consolidate(session_key):
                    self._consolidator.consolidate(session_key)
            except Exception:
                pass  # Silently skip consolidation on error

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
