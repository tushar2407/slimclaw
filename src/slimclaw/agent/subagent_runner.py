"""Subagent runner - runs a child SlimclawAgent to completion in a background thread."""

import hashlib
import queue
import threading
from typing import Optional


from slimclaw.agent.subagent_types import (
    SubAgentContext,
    SubAgentResult,
)
from slimclaw.agent.subagent_utils import get_agent_definition, _resolve_tools


class SubAgentRunner:
    """Runs a child SlimclawAgent to completion in a background thread."""

    DEFAULT_TIMEOUT = 300.0

    def __init__(self, ctx: SubAgentContext) -> None:
        self._ctx = ctx

    def run_sync(
        self,
        task: str,
        agent_type: str = "default",
        timeout: Optional[float] = None,
    ) -> SubAgentResult:
        """
        Spin up a child agent, run it to completion, and block until done.
        Errors are captured and returned — never raised.
        """
        timeout = min(timeout or self.DEFAULT_TIMEOUT, self.DEFAULT_TIMEOUT)
        result_holder: list[SubAgentResult] = []
        child_session_key = self._build_child_session_key(agent_type)

        thread = threading.Thread(
            target=self._run_child,
            args=(task, agent_type, child_session_key, result_holder),
            daemon=True,
            name=f"subagent-d{self._ctx.depth + 1}",
        )
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            return SubAgentResult(
                success=False,
                response="",
                error=f"Subagent timed out after {int(timeout)}s.",
            )

        if not result_holder:
            return SubAgentResult(
                success=False,
                response="",
                error="Subagent thread completed without a result.",
            )

        return result_holder[0]

    def _run_child(
        self,
        task: str,
        agent_type: str,
        child_session_key: str,
        result_holder: list,
    ) -> None:
        """
        Thread target. SlimclawAgent is imported here (not at module level) to
        avoid the circular import: subagent_runner.py → core.py → subagent_runner.py.
        """
        from slimclaw.agent.core import SlimclawAgent  # deferred — circular dep
        from slimclaw.config import load_config

        try:
            agent_def = get_agent_definition(agent_type)

            child_config = {
                **load_config(),
                "shell": {"auto_run": True},
            }

            child_ctx = SubAgentContext(
                parent_session_key=child_session_key,
                depth=self._ctx.depth + 1,
                event_queue=self._ctx.event_queue,
                max_depth=self._ctx.max_depth,
            )

            child_agent = SlimclawAgent(
                config=child_config,
                spawn_ctx=child_ctx,
                tools_override=_resolve_tools(agent_def),
            )
            child_agent.new_session(child_session_key)

            final_response: Optional[str] = None

            for event in child_agent.stream(task):
                try:
                    self._ctx.event_queue.put_nowait(event)
                except queue.Full:
                    pass

                if event.type == "complete":
                    final_response = event.data.response

            result_holder.append(
                SubAgentResult(success=True, response=final_response or "(no response)")
            )

        except Exception as exc:  # noqa: BLE001
            result_holder.append(
                SubAgentResult(success=False, response="", error=str(exc))
            )

    def _build_child_session_key(self, agent_type: str) -> str:
        """
        Deterministic child session key derived from parent key + agent type + depth.
        Format: agent:<type>:subagent:user:<8-char-hash>:depth:<N>
        """
        raw = f"{self._ctx.parent_session_key}:{agent_type}:{self._ctx.depth + 1}"
        short_hash = hashlib.md5(raw.encode()).hexdigest()[:8]
        return (
            f"agent:{agent_type}:subagent:user:{short_hash}:depth:{self._ctx.depth + 1}"
        )
