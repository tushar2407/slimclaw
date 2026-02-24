"""Type definitions for tools."""

from dataclasses import dataclass


@dataclass
class ToolResult:
    """Structured result for tool calls."""

    success: bool
    data: str = ""
    error: str | None = None
    error_type: str | None = None  # "not_found", "permission", "timeout", etc.
    recoverable: bool = True

    def __str__(self) -> str:
        if self.success:
            return self.data
        prefix = "ERROR" if self.recoverable else "FATAL"
        return f"{prefix} [{self.error_type}]: {self.error}"


def ok(data: str) -> str:
    """Shorthand for successful result."""
    return str(ToolResult(success=True, data=data))


def err(message: str, error_type: str = "unknown", recoverable: bool = True) -> str:
    """Shorthand for error result."""
    return str(
        ToolResult(
            success=False, error=message, error_type=error_type, recoverable=recoverable
        )
    )
