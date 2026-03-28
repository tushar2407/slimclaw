"""Cron store - thread-safe persistence for jobs.json."""

import json
import threading

from slimclaw.config.constants import JOBS_FILE
from slimclaw.cron.types import Job

_lock = threading.Lock()


# ─── Internal (unlocked) helpers ──────────────────────────────────────────────


def _load_unlocked() -> list[Job]:
    if not JOBS_FILE.exists():
        return []
    try:
        data = json.loads(JOBS_FILE.read_text())
        return [Job.from_dict(d) for d in data]
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def _save_unlocked(jobs: list[Job]) -> None:
    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    JOBS_FILE.write_text(json.dumps([j.to_dict() for j in jobs], indent=2))


# ─── Public API ───────────────────────────────────────────────────────────────


def load_jobs() -> list[Job]:
    with _lock:
        return _load_unlocked()


def save_jobs(jobs: list[Job]) -> None:
    with _lock:
        _save_unlocked(jobs)


def add_job(job: Job) -> None:
    with _lock:
        jobs = _load_unlocked()
        _save_unlocked([*jobs, job])


def remove_job(job_id: str) -> bool:
    with _lock:
        jobs = _load_unlocked()
        filtered = [j for j in jobs if j.id != job_id]
        if len(filtered) == len(jobs):
            return False
        _save_unlocked(filtered)
        return True


def update_job(job: Job) -> None:
    with _lock:
        jobs = _load_unlocked()
        updated = [job if j.id == job.id else j for j in jobs]
        _save_unlocked(updated)
