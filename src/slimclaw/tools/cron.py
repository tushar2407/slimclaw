"""Cron tools - schedule, list, and cancel reminders."""

import datetime
import uuid

from langchain_core.tools import tool

from slimclaw.cron import Job, add_job, load_jobs, remove_job


# ─── Time parsing ─────────────────────────────────────────────────────────────

_TIME_FORMATS = [
    "%H:%M",
    "%I:%M %p",
    "%I:%M%p",
    "%I %p",
]


def _parse_when(when: str) -> datetime.datetime | None:
    """Parse a time/datetime string. Bare times are assumed to be today."""
    try:
        return datetime.datetime.fromisoformat(when)
    except ValueError:
        pass

    today = datetime.date.today()
    normalized = when.strip().upper()
    for fmt in _TIME_FORMATS:
        try:
            t = datetime.datetime.strptime(normalized, fmt)
            return datetime.datetime.combine(today, t.time())
        except ValueError:
            continue

    return None


# ─── Tools ────────────────────────────────────────────────────────────────────


@tool
def schedule_reminder(when: str, message: str) -> str:
    """Schedule a one-time reminder. 'when' accepts HH:MM (24h), H:MM AM/PM, or ISO datetime. 'message' is the notification text."""
    parsed = _parse_when(when)
    if parsed is None:
        return (
            f"Could not parse time: '{when}'. "
            "Use HH:MM (24h), H:MM AM/PM, or YYYY-MM-DDTHH:MM:SS."
        )

    now = datetime.datetime.now()
    if parsed < now - datetime.timedelta(minutes=1):
        return (
            f"Time {when} has already passed. Current time is {now.strftime('%H:%M')}."
        )

    job = Job(
        id=uuid.uuid4().hex[:8],
        job_type="once",
        message=message,
        created_at=now.isoformat(),
        trigger_at=parsed.isoformat(),
    )
    add_job(job)
    return (
        f"Reminder scheduled (id: {job.id}) "
        f'for {parsed.strftime("%Y-%m-%d %H:%M")} — "{message}"'
    )


@tool
def list_reminders() -> str:
    """List all scheduled reminders and recurring tasks with their IDs."""
    jobs = load_jobs()
    if not jobs:
        return "No reminders or scheduled tasks."

    lines = []
    for job in jobs:
        if job.job_type == "once":
            lines.append(f"[{job.id}] once | {job.trigger_at} | {job.message}")
        else:
            last = job.last_run or "never"
            lines.append(
                f"[{job.id}] recurring | {job.cron_expr} | {job.message} (last: {last})"
            )
    return "\n".join(lines)


@tool
def cancel_reminder(job_id: str) -> str:
    """Cancel a scheduled reminder by its job ID."""
    found = remove_job(job_id)
    if found:
        return f"Reminder {job_id} cancelled."
    return f"No reminder found with id '{job_id}'."
