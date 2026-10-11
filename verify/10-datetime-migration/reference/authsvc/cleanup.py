"""Nightly cleanup of stale rows. The database returns UTC timestamps without a zone."""
from datetime import datetime, timedelta, timezone

DB_FORMAT = "%Y-%m-%d %H:%M:%S"


def expired_rows(rows: list[dict], max_age_days: int = 30) -> list[int]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    return [row["id"] for row in rows if datetime.strptime(row["updated"], DB_FORMAT).replace(tzinfo=timezone.utc) < cutoff]


def cutoff_string(max_age_days: int = 30) -> str:
    """Parameter for: DELETE FROM sessions WHERE updated < ?"""
    return (datetime.now(timezone.utc) - timedelta(days=max_age_days)).strftime(DB_FORMAT)
