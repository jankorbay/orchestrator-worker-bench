"""Compare the agent's next_run with the reference on random expressions and dates.

Run from a folder holding the agent's cron.py and the reference as reference_impl.py.
Prints "<agree> <done> <total>" lines; the last line is the result.
"""
import random
from datetime import datetime, timedelta

import cron as agent
import reference_impl as ref

TOTAL = 2000
RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
BROKEN = ["*/0", "5-1", "x", "1,,2", "-3", "*/", "", "1-", "/5"]
rng = random.Random(20261009)


def item(lo: int, hi: int) -> str:
    r = rng.random()
    if r < 0.25:
        base = "*"
    elif r < 0.55:
        base = str(rng.randint(lo, hi))
    else:
        a = rng.randint(lo, hi)
        base = f"{a}-{rng.randint(a, hi)}"
    if rng.random() < 0.3:
        base += f"/{rng.randint(1, max(1, (hi - lo) // 3))}"
    return base


def field(i: int) -> str:
    lo, hi = RANGES[i]
    if rng.random() < 0.4:
        return "*"
    return ",".join(item(lo, hi) for _ in range(rng.choice([1, 1, 1, 2, 3])))


def expression() -> str:
    fields = [field(i) for i in range(5)]
    r = rng.random()
    if r < 0.05:
        fields[rng.randrange(5)] = rng.choice(BROKEN)
    elif r < 0.08:
        i = rng.randrange(5)
        fields[i] = str(RANGES[i][1] + 1)
    elif r < 0.10:
        fields = fields[:4] if rng.random() < 0.5 else fields + ["*"]
    return " ".join(fields)


def moment() -> datetime:
    start = datetime(2024, 1, 1)
    return start + timedelta(seconds=rng.randrange(8 * 365 * 86400), microseconds=rng.randrange(10**6))


def outcome(fn, expr: str, after: datetime):
    try:
        return ("ok", fn(expr, after))
    except ValueError:
        return ("ValueError",)
    except Exception as e:  # any other exception is a wrong answer, not a harness crash
        return ("crash", type(e).__name__)


agree = 0
for done in range(1, TOTAL + 1):
    expr, after = expression(), moment()
    agree += outcome(agent.next_run, expr, after) == outcome(ref.next_run, expr, after)
    if done % 50 == 0 or done == TOTAL:
        print(agree, done, TOTAL, flush=True)
