"""Notification dispatch - macOS / Linux / stderr fallback."""

import platform
import subprocess
import sys


def send_notification(title: str, message: str) -> None:
    """Send a desktop notification. Always prints to stderr as fallback."""
    # Sanitize to prevent AppleScript injection
    safe_title = title.replace("\\", "").replace('"', "'")
    safe_message = message.replace("\\", "").replace('"', "'")

    system = platform.system()
    try:
        if system == "Darwin":
            script = f'display notification "{safe_message}" with title "{safe_title}"'
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=5,
            )
        elif system == "Linux":
            subprocess.run(
                ["notify-send", safe_title, safe_message],
                capture_output=True,
                timeout=5,
            )
    except Exception:
        pass  # fallback below always runs

    print(f"\n[SlimClaw reminder] {title}: {message}", file=sys.stderr, flush=True)
