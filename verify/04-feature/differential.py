"""Compare the agent's TTLCache with the reference on random operation sequences.

Run from a folder holding the agent's ttlcache.py and the reference as reference_impl.py.
Prints "<agree> <done> <total>" lines; the last line is the result. A sequence agrees only
if every operation returns the same thing in both implementations.
"""
import random

import reference_impl as ref
import ttlcache as agent

TOTAL = 500
STEPS = 60
rng = random.Random(20261009)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def outcome(fn, *args):
    try:
        return ("ok", fn(*args))
    except Exception as e:
        return ("raised", type(e).__name__)


def scenario() -> tuple:
    """Drawn up front so every agent sees the same sequences, whatever it returns."""
    ops = [(rng.choice(["set", "set", "get", "get", "delete", "len", "in", "stats", "tick"]),
            rng.choice("abcdef"), rng.randint(0, 99), rng.choice([0.5, 1, 1, 2, 3])) for _ in range(STEPS)]
    return rng.randint(1, 4), rng.choice([1, 2, 5, 10]), ops


def same_run(capacity: int, ttl: float, ops: list) -> bool:
    clocks = Clock(), Clock()
    caches = agent.TTLCache(capacity, ttl, clocks[0]), ref.TTLCache(capacity, ttl, clocks[1])
    for op, key, value, dt in ops:
        if op == "tick":
            for c in clocks:
                c.now += dt
            continue
        results = []
        for cache in caches:
            results.append({
                "set": lambda: outcome(cache.set, key, value),
                "get": lambda: outcome(cache.get, key, "<missing>"),
                "delete": lambda: outcome(cache.delete, key),
                "len": lambda: outcome(len, cache),
                "in": lambda: outcome(lambda: key in cache),
                "stats": lambda: outcome(cache.stats),
            }[op]())
        if results[0] != results[1]:
            return False
    return True


agree = 0
scenarios = [scenario() for _ in range(TOTAL)]
for done, (capacity, ttl, ops) in enumerate(scenarios, 1):
    try:
        agree += same_run(capacity, ttl, ops)
    except Exception:  # constructor or harness-level crash in the agent's code
        pass
    if done % 25 == 0 or done == TOTAL:
        print(agree, done, TOTAL, flush=True)
