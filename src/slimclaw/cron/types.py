"""Cron types - Job dataclass for scheduled tasks."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Job:
    id: str
    job_type: Literal["once", "recurring"]
    message: str
    created_at: str  # ISO 8601
    trigger_at: str | None = None  # ISO 8601, for once jobs
    cron_expr: str | None = None  # "min hour day month weekday", for recurring
    last_run: str | None = None  # ISO 8601, for recurring dedup

    def __post_init__(self) -> None:
        if self.job_type == "once" and self.trigger_at is None:
            raise ValueError("once jobs require trigger_at")
        if self.job_type == "recurring" and self.cron_expr is None:
            raise ValueError("recurring jobs require cron_expr")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_type": self.job_type,
            "message": self.message,
            "created_at": self.created_at,
            "trigger_at": self.trigger_at,
            "cron_expr": self.cron_expr,
            "last_run": self.last_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Job":
        return cls(
            id=d["id"],
            job_type=d["job_type"],
            message=d["message"],
            created_at=d["created_at"],
            trigger_at=d.get("trigger_at"),
            cron_expr=d.get("cron_expr"),
            last_run=d.get("last_run"),
        )
