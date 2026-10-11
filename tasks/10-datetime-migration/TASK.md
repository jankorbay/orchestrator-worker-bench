# Task 10 — Move `authsvc` off deprecated UTC datetimes

`datetime.utcnow()` and `datetime.utcfromtimestamp()` are deprecated since Python 3.12
and return naive datetimes. Migrate the `authsvc` package to timezone-aware UTC:

1. No use of `utcnow` or `utcfromtimestamp` may remain anywhere in the project (code,
   comments, tests).
2. Every datetime the package creates, returns or keeps in memory is timezone-aware UTC.
   That includes values parsed back from strings or unix timestamps. Functions that take a
   datetime are called with aware UTC datetimes.
3. Everything that leaves the process must keep exactly its current format: wire strings
   (`2026-10-09T12:00:00Z`), audit timestamps (`2026-10-09T12:00:00.123456Z`), database
   strings (`2026-10-09 12:00:00`), unix timestamps, quota keys.
4. Use `datetime.timezone.utc` so the code keeps working on Python 3.10.

`test_authsvc.py` holds the current tests; keep them passing and update them to the new
behaviour where needed.

Run tests with: `python3 -m unittest -q` (from this directory).
