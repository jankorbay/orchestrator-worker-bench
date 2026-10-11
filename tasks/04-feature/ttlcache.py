"""TTL + LRU cache. See TASK.md for the spec."""
import time


class TTLCache:
    def __init__(self, capacity: int, ttl: float, clock=time.monotonic):
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def set(self, key, value) -> None:
        raise NotImplementedError

    def delete(self, key) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __contains__(self, key) -> bool:
        raise NotImplementedError

    def stats(self) -> dict:
        raise NotImplementedError
