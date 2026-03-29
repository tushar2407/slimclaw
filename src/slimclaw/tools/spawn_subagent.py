"""Subagent tool factory - creates the spawn_agent StructuredTool."""

from langchain_core.tools import StructuredTool

from slimclaw.agent.subagent_runner import SubAgentRunner
from slimclaw.agent.subagent_types import SubAgentContext


def make_spawn_agent_tool(ctx: SubAgentContext) -> StructuredTool:
    """
    Returns a spawn_agent StructuredTool bound to the given SubAgentContext.
    Called once per agent instantiation from SlimclawAgent._build_graph().
    """

    def spawn_agent(
        task: str,
        agent_type: str = "default",
        timeout: int = 300,
    ) -> str:
        """
        Delegate a task to a specialised subagent and return its response.

        Args:
            task: Full task description for the subagent. Be specific and self-contained.
            agent_type: Agent type defined in AGENTS.md, or 'default'.
            timeout: Max seconds to wait (capped at 300).

        Returns:
            The subagent's final response as a string.
        """
        if ctx.depth >= ctx.max_depth:
            return (
                f"ERROR: max agent depth ({ctx.max_depth}) reached. "
                "Complete this task directly instead of spawning another agent."
            )

        result = SubAgentRunner(ctx).run_sync(
            task,
            agent_type=agent_type,
            timeout=float(min(timeout, 300)),
        )

        if not result.success:
            return f"Subagent failed: {result.error}"
        return result.response

    depth_remaining = ctx.max_depth - ctx.depth
    return StructuredTool.from_function(
        spawn_agent,
        name="spawn_agent",
        description=(
            "Delegate a complex subtask to a specialised subagent and get its response. "
            "Use when a task benefits from focused expertise or isolation. "
            f"Depth {ctx.depth}/{ctx.max_depth} — {depth_remaining} level(s) remaining. "
            "Available agent types are defined in ~/.slimclaw/AGENTS.md."
        ),
    )
