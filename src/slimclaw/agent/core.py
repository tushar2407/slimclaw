"""SlimClaw Agent - class-based agent with checkpointing and streaming."""

import queue as queue_module
from typing import Generator, Optional

from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from slimclaw.agent.state import AgentState
from slimclaw.agent.subagent_types import SubAgentContext
from slimclaw.agent.types import InvokeResult, PendingToolCall, StreamEvent
from slimclaw.agent.utils import build_env_context
from slimclaw.config import SLIMCLAW_DIR, load_config
from slimclaw.llm import Model, create_llm
from slimclaw.prompt import PromptContext, build_system_prompt
from slimclaw.tools import TOOLS


class SlimclawAgent:
    """
    Stateful agent with checkpointing and interrupt/resume support.

    Usage:
        agent = SlimclawAgent()
        agent.new_session("session-123")

        for event in agent.stream("list files"):
            if event.type == "interrupt":
                # Handle shell confirmation
                if user_approves:
                    for event in agent.resume():
                        handle(event)
            elif event.type == "complete":
                print(event.data.response)
    """

    def __init__(
        self,
        config: Optional[dict] = None,
        spawn_ctx: Optional[SubAgentContext] = None,
        tools_override: Optional[list] = None,
        child_event_queue: Optional["queue_module.Queue"] = None,
    ):
        self._config = config if config is not None else load_config()
        self._checkpointer = MemorySaver()
        self._session_id: Optional[str] = None
        self._graph = None  # Lazy init
        self._llm = None
        self._spawn_ctx = spawn_ctx
        self._tools_override = tools_override
        self._child_event_queue = child_event_queue

    def _build_graph(self):
        """Build the LangGraph agent with checkpointing."""
        from slimclaw.tools.subagent import make_spawn_agent_tool

        model = Model.from_config(self._config.get("llm", {}))
        self._llm = create_llm(model)

        # Build prompt context
        env = build_env_context()
        soul = (
            (SLIMCLAW_DIR / "SOUL.md").read_text()
            if (SLIMCLAW_DIR / "SOUL.md").exists()
            else ""
        )
        memory = (
            (SLIMCLAW_DIR / "MEMORY.md").read_text()
            if (SLIMCLAW_DIR / "MEMORY.md").exists()
            else ""
        )

        # Start from override (child agent) or global TOOLS (top-level agent)
        tools = list(
            self._tools_override if self._tools_override is not None else TOOLS
        )

        # Inject spawn_agent if depth allows
        if self._spawn_ctx is None:
            # Top-level agent: create root SubAgentContext
            q = self._child_event_queue or queue_module.Queue()
            self._spawn_ctx = SubAgentContext(
                parent_session_key=self._session_id or "unknown",
                depth=0,
                event_queue=q,
                max_depth=2,
            )

        if self._spawn_ctx.depth < self._spawn_ctx.max_depth:
            tools.append(make_spawn_agent_tool(self._spawn_ctx))

        ctx = PromptContext(
            env=env,
            tools=tools,
            soul=soul,
            memory=memory,
            cwd=env.get("cwd", ""),
        )

        self._graph = create_react_agent(
            self._llm,
            tools,
            prompt=build_system_prompt(ctx),
            checkpointer=self._checkpointer,
            interrupt_before=["tools"],  # Pause before any tool execution
        )

    def new_session(self, session_id: str) -> None:
        """Start a new conversation session."""
        self._session_id = session_id
        # Keep spawn context in sync with the current session key
        if self._spawn_ctx is not None:
            self._spawn_ctx = SubAgentContext(
                parent_session_key=session_id,
                depth=self._spawn_ctx.depth,
                event_queue=self._spawn_ctx.event_queue,
                max_depth=self._spawn_ctx.max_depth,
            )
        # Rebuild graph to refresh env context (cwd, datetime, etc.)
        self._build_graph()

    def _get_config(self) -> dict:
        """Get LangGraph config with thread_id."""
        return {"configurable": {"thread_id": self._session_id}}

    def _needs_approval(self, pending: list[PendingToolCall]) -> bool:
        """Check if any pending tool needs user approval."""
        auto_run = self._config.get("shell", {}).get("auto_run")

        for tool in pending:
            if tool.tool_name == "shell":
                # None = ask, True = always allow, False = always deny
                if auto_run is not True:
                    return True
        return False

    def _extract_pending_tools(self, state) -> list[PendingToolCall]:
        """Extract pending tool calls from graph state."""
        pending = []
        messages = state.values.get("messages", [])

        # Find the last AI message with tool calls
        for msg in reversed(messages):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    pending.append(
                        PendingToolCall(
                            tool_name=tc["name"],
                            tool_args=tc.get("args", {}),
                            tool_call_id=tc.get("id", ""),
                        )
                    )
                break

        return pending

    def _extract_response(self, messages: list) -> Optional[str]:
        """Extract the final text response from messages."""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                # Skip tool messages
                if not hasattr(msg, "name") or not msg.name:
                    return msg.content
        return None

    def stream(self, user_input: str) -> Generator[StreamEvent, None, None]:
        """
        Stream agent execution, yielding events.

        Yields:
            StreamEvent with types:
            - "tool_call": About to call a tool (data=PendingToolCall)
            - "tool_result": Tool returned (data={"tool": name, "result": content})
            - "text": Agent text response (data=str)
            - "interrupt": Needs user approval (data=InvokeResult)
            - "complete": Execution finished (data=InvokeResult)
        """
        if not self._graph or not self._session_id:
            raise RuntimeError("Call new_session() before stream()")

        config = self._get_config()
        messages = [HumanMessage(content=user_input)]

        # Stream the agent execution
        for event in self._graph.stream(
            {"messages": messages}, config, stream_mode="updates"
        ):
            for node, data in event.items():
                if not isinstance(data, dict):
                    continue
                msgs = data.get("messages", [])
                for msg in msgs:
                    # Tool call from agent
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            yield StreamEvent(
                                type="tool_call",
                                data=PendingToolCall(
                                    tool_name=tc["name"],
                                    tool_args=tc.get("args", {}),
                                    tool_call_id=tc.get("id", ""),
                                ),
                            )

                    # Tool result
                    elif hasattr(msg, "name") and msg.name:
                        content = getattr(msg, "content", "") or ""
                        yield StreamEvent(
                            type="tool_result",
                            data={"tool": msg.name, "result": content},
                        )

                    # Agent text response
                    elif hasattr(msg, "content") and msg.content and node == "agent":
                        yield StreamEvent(type="text", data=msg.content)

        # Check if we're interrupted (pending tools)
        state = self._graph.get_state(config)

        if state.next:  # Has pending steps
            pending = self._extract_pending_tools(state)

            if self._needs_approval(pending):
                # Interrupted - needs user approval
                yield StreamEvent(
                    type="interrupt",
                    data=InvokeResult(
                        response=None,
                        state=AgentState.INTERRUPTED,
                        pending_tools=pending,
                    ),
                )
                return
            else:
                # Auto-approve non-shell tools and continue
                yield from self.resume()
                return

        # Completed
        all_messages = state.values.get("messages", [])
        yield StreamEvent(
            type="complete",
            data=InvokeResult(
                response=self._extract_response(all_messages),
                state=AgentState.COMPLETED,
                pending_tools=[],
            ),
        )

    def resume(self) -> Generator[StreamEvent, None, None]:
        """
        Resume execution after user approval.

        Yields the same StreamEvent types as stream().
        """
        if not self._graph or not self._session_id:
            raise RuntimeError("No active session to resume")

        config = self._get_config()

        # Resume from checkpoint (pass None to continue)
        for event in self._graph.stream(None, config, stream_mode="updates"):
            for node, data in event.items():
                if not isinstance(data, dict):
                    continue
                msgs = data.get("messages", [])
                for msg in msgs:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            yield StreamEvent(
                                type="tool_call",
                                data=PendingToolCall(
                                    tool_name=tc["name"],
                                    tool_args=tc.get("args", {}),
                                    tool_call_id=tc.get("id", ""),
                                ),
                            )

                    elif hasattr(msg, "name") and msg.name:
                        content = getattr(msg, "content", "") or ""
                        yield StreamEvent(
                            type="tool_result",
                            data={"tool": msg.name, "result": content},
                        )

                    elif hasattr(msg, "content") and msg.content and node == "agent":
                        yield StreamEvent(type="text", data=msg.content)

        # Check state again
        state = self._graph.get_state(config)

        if state.next:
            pending = self._extract_pending_tools(state)
            if self._needs_approval(pending):
                yield StreamEvent(
                    type="interrupt",
                    data=InvokeResult(
                        response=None,
                        state=AgentState.INTERRUPTED,
                        pending_tools=pending,
                    ),
                )
                return
            else:
                yield from self.resume()
                return

        all_messages = state.values.get("messages", [])
        yield StreamEvent(
            type="complete",
            data=InvokeResult(
                response=self._extract_response(all_messages),
                state=AgentState.COMPLETED,
                pending_tools=[],
            ),
        )

    def cancel(self) -> InvokeResult:
        """
        Cancel pending tool calls.

        Injects ToolMessages for cancelled tools into graph state,
        then returns an InvokeResult indicating cancellation.
        """
        if not self._graph or not self._session_id:
            return InvokeResult(
                response="No active session.",
                state=AgentState.COMPLETED,
                pending_tools=[],
            )

        config = self._get_config()
        state = self._graph.get_state(config)
        messages = state.values.get("messages", [])

        # Find pending tool calls from the last AIMessage
        tool_messages = []
        for msg in reversed(messages):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_messages.append(
                        ToolMessage(
                            content="Cancelled by user.",
                            tool_call_id=tc.get("id", ""),
                            name=tc.get("name", ""),
                        )
                    )
                break

        # Update graph state with cancellation messages
        if tool_messages:
            self._graph.update_state(config, {"messages": tool_messages})

        return InvokeResult(
            response="Command cancelled by user.",
            state=AgentState.COMPLETED,
            pending_tools=[],
        )
