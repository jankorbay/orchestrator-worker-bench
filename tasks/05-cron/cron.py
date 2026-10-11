"""Cron schedule evaluation. See TASK.md for the spec."""
from datetime import datetime


def next_run(expr: str, after: datetime) -> datetime:
    raise NotImplementedError
