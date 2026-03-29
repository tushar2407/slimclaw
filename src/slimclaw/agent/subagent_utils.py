import re

from slimclaw.config import AGENTS_FILE, DEFAULT_AGENT
from slimclaw.agent.subagent_types import AgentDefinition
from slimclaw.tools import TOOLS


def get_agent_definition(name: str) -> AgentDefinition:
    """Return named definition from AGENTS.md, or default if not found."""
    default_agent = AgentDefinition(**DEFAULT_AGENT)
    if not AGENTS_FILE.exists():
        return default_agent
    try:
        definitions = _parse_agents_md(AGENTS_FILE.read_text())
    except Exception:
        return default_agent
    return definitions.get(name, default_agent)


def _parse_agents_md(content: str) -> dict[str, AgentDefinition]:
    definitions: dict[str, AgentDefinition] = {}
    current_name: str | None = None
    current_attrs: dict[str, str] = {}

    for line in content.splitlines():
        stripped = line.strip()
        h2_match = re.match(r"^##\s+(\S+)", stripped)
        if h2_match:
            if current_name:
                definitions[current_name] = _build_definition(
                    current_name, current_attrs
                )
            current_name = h2_match.group(1).lower()
            current_attrs = {}
            continue
        if current_name and ":" in stripped:
            key, _, value = stripped.partition(":")
            current_attrs[key.strip().lower()] = value.strip()

    if current_name:
        definitions[current_name] = _build_definition(current_name, current_attrs)
    return definitions


def _build_definition(name: str, attrs: dict[str, str]) -> AgentDefinition:
    tools_raw = attrs.get("tools", "all")
    tools: list[str] = (
        ["all"]
        if tools_raw.strip().lower() == "all"
        else [t.strip() for t in tools_raw.split(",") if t.strip()]
    )
    return AgentDefinition(
        name=name,
        description=attrs.get("description", ""),
        tools=tools,
        model=attrs.get("model", "inherit"),
    )


def _resolve_tools(agent_def: AgentDefinition) -> list:  # noqa: ANN001
    """
    Return the tool list for a child agent based on its AgentDefinition.

    tools=["all"] → full TOOLS list minus shell (shell must be opted in via AGENTS.md)
    explicit list → only those named tools
    spawn_agent is injected separately by SlimclawAgent._build_graph() based on depth.
    """

    tools_by_name = {t.name: t for t in TOOLS}

    # why was this added?
    # It was a deliberate safety default from the original design: child agents run unattended in a background thread with no user watching, so tools: all in AGENTS.md excludes shell to prevent a child from running destructive commands silently.
    # Shell can still be given to a child — it just has to be opted in explicitly in AGENTS.md:
    # ## coder
    # tools: read, write, edit, shell, grep, find, ls
    # The child also gets shell.auto_run = True injected into its config (in _run_child), so if shell is included it runs without the confirmation prompt that the main agent shows the user.
    # The tradeoff: tools: all is "safe by default" for unattended agents, at the cost of being slightly surprising if someone expects all to mean literally all tools.
    if agent_def.tools == ["all"]:
        return [t for t in TOOLS if t.name != "shell"]

    return [tools_by_name[name] for name in agent_def.tools if name in tools_by_name]
