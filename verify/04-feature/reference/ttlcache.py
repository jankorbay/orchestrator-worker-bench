"""TTL + LRU cache. See TASK.md for the spec."""
import time
from collections import OrderedDict


class TTLCache:
    def __init__(self, capacity: int, ttl: float, clock=time.monotonic):
        if capacity < 1 or ttl <= 0:
            raise ValueError("capacity must be >= 1 and ttl > 0")
        self.capacity, self.ttl, self.clock = capacity, ttl, clock
        self._data = OrderedDict()  # key -> (value, set_time), oldest use first
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _live(self, key) -> bool:
        entry = self._data.get(key)
        if entry is None:
            return False
        if self.clock() - entry[1] >= self.ttl:
            del self._data[key]
            return False
        return True

    def _purge(self) -> None:
        for key in list(self._data):
            self._live(key)

    def get(self, key, default=None):
        if not self._live(key):
            self._stats["misses"] += 1
            return default
        self._stats["hits"] += 1
        self._data.move_to_end(key)
        return self._data[key][0]

    def set(self, key, value) -> None:
        if not self._live(key) and len(self._data) >= self.capacity:
            self._purge()
            if len(self._data) >= self.capacity:
                self._data.popitem(last=False)
                self._stats["evictions"] += 1
        self._data[key] = (value, self.clock())
        self._data.move_to_end(key)

    def delete(self, key) -> bool:
        if not self._live(key):
            return False
        del self._data[key]
        return True

    def __len__(self) -> int:
        self._purge()
        return len(self._data)

    def __contains__(self, key) -> bool:
        return self._live(key)

    def stats(self) -> dict:
        return dict(self._stats)
