"""System prompt builder - assembles sections into a complete prompt."""
from .types import PromptContext
from .sections import (
    build_identity_section,
    build_environment_section,
    build_tooling_section,
    build_behaviour_section,
    build_workspace_section,
    build_persona_section,
)


def build_system_prompt(ctx: PromptContext) -> str:
    """Build the complete system prompt from context.

    Assembles all sections in order, filtering out empty sections.
    """
    sections = [
        build_identity_section(),
        build_environment_section(ctx.env),
        build_tooling_section(ctx.tools),
        build_behaviour_section(),
        build_workspace_section(ctx.cwd),
        build_persona_section(ctx.soul, ctx.memory),
    ]

    # Filter out empty sections and join with double newlines
    return "\n\n".join(s for s in sections if s)
