# Task 04 — Implement `TTLCache`

Implement the class in `ttlcache.py` (stdlib only). Keep the method signatures.

`TTLCache(capacity, ttl, clock=time.monotonic)`
- `capacity` is the max number of live entries, `ttl` is seconds an entry lives after it
  was last **set**. Raise `ValueError` if `capacity < 1` or `ttl <= 0`.
- `clock()` returns the current time in seconds. Tests pass a fake clock; never call
  `time` directly.
- An entry is **expired** when `clock() - set_time >= ttl`. Expired entries behave as if
  absent everywhere (`get`, `in`, `len`, `delete`).
- `get(key, default=None)`: value or `default`. A hit marks the key most recently used.
  It does **not** extend the TTL. `in` does not change recency.
- `set(key, value)`: insert or overwrite. Overwriting resets the TTL and marks the key
  most recently used. If inserting a new key would exceed capacity, first drop all expired
  entries; if still full, evict the least recently used live entry.
- `delete(key)`: remove; return `True` if a live entry was removed, else `False`.
- `len(cache)`: number of live (non-expired) entries.
- `stats()`: `{"hits": int, "misses": int, "evictions": int}`. `get` on a missing or
  expired key is a miss. Only LRU evictions count as evictions (expiry does not).

`test_ttlcache.py` has a couple of starter tests.

Run with: `python3 -m unittest -q` (from this directory).
