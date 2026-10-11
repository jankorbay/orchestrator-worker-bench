"""Cron schedule evaluation. See TASK.md for the spec."""
from datetime import datetime, timedelta

RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]


def _parse_field(text: str, lo: int, hi: int) -> set[int]:
    values = set()
    for item in text.split(","):
        base, _, step = item.partition("/")
        if not step and "/" in item:
            raise ValueError(f"empty step in {item!r}")
        step = int(step) if step else 1  # int() raises ValueError on junk
        if step < 1:
            raise ValueError("step must be >= 1")
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            a, b = base.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = int(base)
            end = hi if "/" in item else start
        if not (lo <= start <= hi and lo <= end <= hi) or start > end:
            raise ValueError(f"bad range in {item!r}")
        values.update(range(start, end + 1, step))
    return values


def next_run(expr: str, after: datetime) -> datetime:
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError("expected 5 fields")
    minutes, hours, doms, months, dows = (
        _parse_field(f, lo, hi) for f, (lo, hi) in zip(fields, RANGES))
    dows = {d % 7 for d in dows}
    either = not fields[2].startswith("*") and not fields[4].startswith("*")

    start = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    day = start.date()
    for _ in range(366 * 10 + 3):
        if day.month in months:
            dom_ok = day.day in doms
            dow_ok = (day.weekday() + 1) % 7 in dows
            if (dom_ok or dow_ok) if either else (dom_ok and dow_ok):
                for h in sorted(hours):
                    for m in sorted(minutes):
                        candidate = datetime(day.year, day.month, day.day, h, m)
                        if candidate >= start:
                            return candidate
        day += timedelta(days=1)
    raise ValueError("no matching time within 10 years")
