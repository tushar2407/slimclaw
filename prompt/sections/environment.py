"""Environment section - runtime context."""


def build_environment_section(env: dict) -> str:
    """Build the environment section with runtime context."""
    if not env:
        return ""

    lines = ["## Environment"]
    for key, value in env.items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)
