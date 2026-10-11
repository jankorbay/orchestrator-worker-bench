from datetime import datetime, timedelta


def next_daily_run(hour: int, now: datetime | None = None) -> datetime:
    """Next time the clock (UTC) shows `hour`:00."""
    now = now or datetime.utcnow()
    run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    return run if run > now else run + timedelta(days=1)


def seconds_until(run_at: datetime) -> float:
    return (run_at - datetime.utcnow()).total_seconds()
