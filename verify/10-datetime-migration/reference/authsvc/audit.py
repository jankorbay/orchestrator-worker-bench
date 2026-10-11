"""In-memory audit log (flushed to the log pipeline elsewhere).

Entry timestamps are ISO 8601 with microseconds and a trailing Z, e.g.
'2026-10-09T12:00:00.123456Z'. The log pipeline parses exactly this format.
"""
from datetime import datetime, timezone

_log: list[dict] = []


def record(actor: str, action: str, **details) -> dict:
    now = datetime.now(timezone.utc)
    entry = {"ts": now.replace(tzinfo=None).isoformat() + "Z", "actor": actor, "action": action, "details": details}
    _log.append(entry)
    return entry


def entries_since(since: datetime) -> list[dict]:
    return [e for e in _log if datetime.fromisoformat(e["ts"].rstrip("Z")).replace(tzinfo=timezone.utc) >= since]


def clear() -> None:
    _log.clear()
