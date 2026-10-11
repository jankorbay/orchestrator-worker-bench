# Task 08 — The job queue misbehaves in production

`jobqueue.py` is the in-process job queue of our thumbnail service. It works in tests,
but in production (8 worker threads, several producer threads) we see:

- some thumbnails are generated twice, and some are never generated;
- duplicate submissions slip through when the upload service retries a request;
- now and then a worker thread dies with `IndexError: pop from an empty deque`;
- the numbers from `stats()` don't add up (e.g. completed + dead ≠ submitted).

Make `JobQueue` and `run_workers` correct under any number of concurrent producer and
worker threads. Keep the public API and the existing single-threaded behaviour. Note the
`JobQueue` docstring: metrics sinks are customer code, may be slow, and may call
`stats()` / `pending_count()` from inside a callback.

Add tests that would have caught this. `test_jobqueue.py` has the current tests.

Run tests with: `python3 -m unittest -q` (from this directory).
