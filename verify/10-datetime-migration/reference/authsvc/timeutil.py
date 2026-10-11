"""Time helpers. Every timestamp we store or send is UTC."""
from datetime import datetime, timezone

WIRE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # API and session store format
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def to_wire(when: datetime) -> str:
    return when.strftime(WIRE_FORMAT)


def from_wire(text: str) -> datetime:
    return datetime.strptime(text, WIRE_FORMAT).replace(tzinfo=timezone.utc)


def to_unix(when: datetime) -> int:
    return int((when - EPOCH).total_seconds())


def from_unix(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, timezone.utc)


def utc_today() -> str:
    """Today's date in UTC, e.g. '2026-10-09'."""
    return datetime.now(timezone.utc).date().isoformat()
