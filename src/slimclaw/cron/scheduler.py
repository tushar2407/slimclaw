"""CronScheduler - background daemon thread for scheduled jobs."""

import datetime
import logging
import threading

from slimclaw.cron import store
from slimclaw.cron.notify import send_notification

logger = logging.getLogger(__name__)


# ─── Cron field matching ───────────────────────────────────────────────────────


def _field_matches(field: str, actual: int) -> bool:
    """Check whether a single cron field matches the actual value."""
    if field == "*":
        return True
    if "," in field:
        return any(_field_matches(part, actual) for part in field.split(","))
    if field.startswith("*/"):
        try:
            step = int(field[2:])
            return actual % step == 0
        except ValueError:
            return False
    if "-" in field:
        parts = field.split("-", 1)
        try:
            return int(parts[0]) <= actual <= int(parts[1])
        except ValueError:
            return False
    try:
        return int(field) == actual
    except ValueError:
        return False


def _cron_matches(expr: str, now: datetime.datetime) -> bool:
    """Check whether a 5-field cron expression matches the given datetime.

    Field order: minute hour day_of_month month day_of_week
    day_of_week: 0=Sunday, 1=Monday, ..., 6=Saturday (standard cron convention)
    Python weekday(): 0=Monday ... 6=Sunday → map: (weekday + 1) % 7
    """
    fields = expr.split()
    if len(fields) != 5:
        return False

    minute, hour, dom, month, dow = fields
    cron_dow = (now.weekday() + 1) % 7  # convert to cron Sunday=0 convention

    return (
        _field_matches(minute, now.minute)
        and _field_matches(hour, now.hour)
        and _field_matches(dom, now.day)
        and _field_matches(month, now.month)
        and _field_matches(dow, cron_dow)
    )


# ─── Scheduler ────────────────────────────────────────────────────────────────


class CronScheduler:
    """Background daemon thread that fires scheduled jobs."""

    def __init__(self, poll_interval: int = 30) -> None:
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="cron-scheduler"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception:
                logger.exception("Scheduler tick failed")
            self._stop_event.wait(self._poll_interval)

    def _tick(self) -> None:
        jobs = store.load_jobs()
        if not jobs:
            return

        now = datetime.datetime.now()
        to_remove: list[str] = []

        for job in jobs:
            try:
                if job.job_type == "once":
                    trigger = datetime.datetime.fromisoformat(job.trigger_at)  # type: ignore[arg-type]
                    if trigger <= now:
                        send_notification("SlimClaw", job.message)
                        to_remove.append(job.id)

                elif job.job_type == "recurring" and job.cron_expr:
                    if _cron_matches(job.cron_expr, now):
                        # Dedup: skip if already ran this minute
                        if job.last_run:
                            last = datetime.datetime.fromisoformat(job.last_run)
                            if last.replace(second=0, microsecond=0) == now.replace(
                                second=0, microsecond=0
                            ):
                                continue
                        send_notification("SlimClaw", job.message)
                        updated = job.__class__(
                            id=job.id,
                            job_type=job.job_type,
                            message=job.message,
                            created_at=job.created_at,
                            trigger_at=job.trigger_at,
                            cron_expr=job.cron_expr,
                            last_run=now.isoformat(),
                        )
                        store.update_job(updated)
            except Exception:
                logger.exception("Failed to process job %s", job.id)

        for job_id in to_remove:
            store.remove_job(job_id)
