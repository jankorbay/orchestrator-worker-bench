"""Per-user daily API quota. Quotas reset at midnight UTC."""
import datetime

_counts: dict[str, int] = {}


def quota_key(user_id: int) -> str:
    return f"{user_id}:{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}"


def hit(user_id: int, limit: int = 100) -> bool:
    """Count one request; False once the user is over today's limit."""
    key = quota_key(user_id)
    _counts[key] = _counts.get(key, 0) + 1
    return _counts[key] <= limit


def reset_time() -> datetime.datetime:
    now = datetime.datetime.now(datetime.timezone.utc)
    return datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc) + datetime.timedelta(days=1)
