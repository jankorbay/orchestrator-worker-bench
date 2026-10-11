"""In-process job queue used by the thumbnail service.

Producers call submit(). Worker threads loop on claim() and then complete() or fail().
run_workers() is the standard worker pool.
"""
import threading
import time
from collections import deque


class NullMetrics:
    """Metrics sink interface. Real sinks are customer code (see JobQueue docstring)."""

    def on_submit(self, job_id): pass

    def on_claim(self, job_id): pass

    def on_complete(self, job_id): pass

    def on_fail(self, job_id, will_retry): pass


class JobQueue:
    """FIFO job queue with dedupe, retries and a dead-letter set.

    Metrics sinks are customer code: they can be slow, and they may call the queue's
    read-only methods (stats(), pending_count()) from inside a callback.
    """

    def __init__(self, max_attempts: int = 3, metrics=None):
        self.max_attempts = max_attempts
        self.metrics = metrics or NullMetrics()
        self._pending = deque()
        self._running = {}  # job_id -> payload
        self._attempts = {}  # job_id -> attempts started so far
        self._done = set()
        self._dead = set()
        self._counts = {"submitted": 0, "completed": 0, "failed": 0, "dead": 0}

    def submit(self, job_id, payload) -> bool:
        """Queue a job. Returns False if this job_id was submitted before (dedupe)."""
        if job_id in self._attempts:
            return False
        self.metrics.on_submit(job_id)
        self._attempts[job_id] = 0
        self._pending.append((job_id, payload))
        self._counts["submitted"] += 1
        return True

    def claim(self):
        """Take the next pending job as (job_id, payload), or None if nothing is pending."""
        if not self._pending:
            return None
        job_id, payload = self._pending[0]
        self.metrics.on_claim(job_id)
        self._pending.popleft()
        self._running[job_id] = payload
        self._attempts[job_id] += 1
        return job_id, payload

    def complete(self, job_id) -> None:
        """Mark a claimed job as done."""
        if job_id not in self._running:
            raise KeyError(job_id)
        del self._running[job_id]
        self._done.add(job_id)
        self._counts["completed"] += 1
        self.metrics.on_complete(job_id)

    def fail(self, job_id) -> None:
        """Mark a claimed job as failed: retry it, or dead-letter it after max_attempts."""
        payload = self._running.pop(job_id)
        self._counts["failed"] += 1
        will_retry = self._attempts[job_id] < self.max_attempts
        self.metrics.on_fail(job_id, will_retry)
        if will_retry:
            self._pending.append((job_id, payload))
        else:
            self._dead.add(job_id)
            self._counts["dead"] += 1

    def pending_count(self) -> int:
        return len(self._pending)

    def dead_jobs(self) -> set:
        return set(self._dead)

    def stats(self) -> dict:
        return dict(self._counts, pending=len(self._pending), running=len(self._running))


def run_workers(queue: JobQueue, handler, n_workers: int = 8, idle_timeout: float = 0.2) -> None:
    """Run handler(job_id, payload) for every job with n_workers threads.

    A handler exception counts as a failure. Returns once the queue has stayed empty for
    idle_timeout seconds.
    """
    def work():
        idle_since = time.monotonic()
        while time.monotonic() - idle_since < idle_timeout:
            job = queue.claim()
            if job is None:
                time.sleep(0.001)
                continue
            job_id, payload = job
            try:
                handler(job_id, payload)
            except Exception:
                queue.fail(job_id)
            else:
                queue.complete(job_id)
            idle_since = time.monotonic()

    threads = [threading.Thread(target=work, name=f"worker-{i}") for i in range(n_workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
