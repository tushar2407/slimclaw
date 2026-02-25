"""Persona section - SOUL.md and MEMORY.md content."""


def build_persona_section(soul: str, memory: str) -> str:
    """Build the persona section with SOUL.md and MEMORY.md content."""
    parts = []

    if soul and soul.strip():
        parts.append(f"## Persona\n{soul.strip()}")

    if memory and memory.strip():
        parts.append(f"## Memory\n{memory.strip()}")

    return "\n\n".join(parts)
