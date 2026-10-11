import sys
import threading
import time
import unittest
from collections import Counter

from jobqueue import JobQueue, run_workers

TIMEOUT = 20  # seconds; a deadlock fails the test instead of hanging the suite


class YieldingMetrics:
    """A slow customer sink: gives up the GIL in every callback, so races show up."""

    def on_submit(self, job_id): time.sleep(0)

    def on_claim(self, job_id): time.sleep(0)

    def on_complete(self, job_id): time.sleep(0)

    def on_fail(self, job_id, will_retry): time.sleep(0)


class ReentrantMetrics(YieldingMetrics):
    """A sink that reads queue stats from inside callbacks (allowed by the docstring)."""

    def __init__(self):
        self.queue = None
        self.snapshots = 0

    def _peek(self):
        self.queue.stats()
        self.queue.pending_count()
        self.snapshots += 1
        time.sleep(0)

    def on_submit(self, job_id): self._peek()

    def on_claim(self, job_id): self._peek()

    def on_complete(self, job_id): self._peek()

    def on_fail(self, job_id, will_retry): self._peek()


def within_timeout(fn):
    """Run fn in a daemon thread. Returns (finished, exceptions raised in any thread)."""
    errors = []
    old_hook = threading.excepthook
    threading.excepthook = lambda args: errors.append(args.exc_type.__name__)
    try:
        t = threading.Thread(target=fn, daemon=True)
        t.start()
        t.join(TIMEOUT)
        return not t.is_alive(), errors
    finally:
        threading.excepthook = old_hook


class Concurrency(unittest.TestCase):
    def setUp(self):
        self.old_interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-5)

    def tearDown(self):
        sys.setswitchinterval(self.old_interval)

    def test_every_job_runs_exactly_once(self):
        q = JobQueue(metrics=YieldingMetrics())
        for i in range(1500):
            q.submit(i, i)
        calls = []
        finished, errors = within_timeout(lambda: run_workers(q, lambda j, p: calls.append(j), n_workers=8))
        self.assertTrue(finished, "workers did not finish (deadlock?)")
        self.assertEqual(errors, [])
        counts = Counter(calls)
        self.assertEqual(set(counts), set(range(1500)), "some jobs never ran")
        self.assertEqual(max(counts.values()), 1, "some jobs ran more than once")
        self.assertEqual(q.stats(), {"submitted": 1500, "completed": 1500, "failed": 0, "dead": 0,
                                     "pending": 0, "running": 0})

    def test_concurrent_duplicate_submissions(self):
        q = JobQueue(metrics=YieldingMetrics())
        accepted = []

        def producer():
            for i in range(300):
                if q.submit(f"upload-{i}", i):
                    accepted.append(i)

        def all_producers():
            threads = [threading.Thread(target=producer) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        finished, errors = within_timeout(all_producers)
        self.assertTrue(finished)
        self.assertEqual(errors, [])
        self.assertEqual(sorted(accepted), list(range(300)), "a duplicate was accepted or a job was lost")
        self.assertEqual(q.pending_count(), 300)
        self.assertEqual(q.stats()["submitted"], 300)

    def test_retries_and_dead_letters_add_up(self):
        q = JobQueue(max_attempts=3, metrics=YieldingMetrics())
        for i in range(600):
            q.submit(i, i)
        attempts = Counter()
        lock = threading.Lock()

        def handler(job_id, payload):
            with lock:
                attempts[job_id] += 1
                n = attempts[job_id]
            if job_id % 3 == 0:
                raise RuntimeError("always fails")
            if job_id % 3 == 1 and n < 2:
                raise RuntimeError("fails once")

        finished, errors = within_timeout(lambda: run_workers(q, handler, n_workers=8))
        self.assertTrue(finished)
        self.assertEqual(errors, [])
        self.assertEqual(q.dead_jobs(), {i for i in range(600) if i % 3 == 0})
        self.assertEqual(q.stats(), {"submitted": 600, "completed": 400, "failed": 200 * 3 + 200,
                                     "dead": 200, "pending": 0, "running": 0})
        self.assertEqual({j for j, n in attempts.items() if n > 3}, set(), "a job ran after it was dead-lettered")

    def test_metrics_may_read_stats_from_callbacks(self):
        metrics = ReentrantMetrics()
        q = JobQueue(metrics=metrics)
        metrics.queue = q

        def go():
            for i in range(300):
                q.submit(i, i)
            run_workers(q, lambda j, p: None, n_workers=8)

        finished, errors = within_timeout(go)
        self.assertTrue(finished, "deadlock when a metrics sink calls stats()")
        self.assertEqual(errors, [])
        self.assertEqual(q.stats()["completed"], 300)
        self.assertGreater(metrics.snapshots, 0)

    def test_claim_never_raises_when_racing_for_the_last_job(self):
        def go():
            for round_ in range(300):
                q = JobQueue(metrics=YieldingMetrics())
                q.submit(round_, None)
                claims = []
                threads = [threading.Thread(target=lambda: claims.append(q.claim())) for _ in range(4)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                got = [c for c in claims if c is not None]
                if len(got) != 1:
                    raise AssertionError(f"{len(got)} workers got the single job")

        finished, errors = within_timeout(go)
        self.assertTrue(finished)
        self.assertEqual(errors, [])


class SingleThreadedUnchanged(unittest.TestCase):
    def test_api(self):
        q = JobQueue(max_attempts=2)
        self.assertTrue(q.submit("a", 1))
        self.assertFalse(q.submit("a", 2))
        self.assertEqual(q.claim(), ("a", 1))
        q.fail("a")
        self.assertEqual(q.pending_count(), 1)
        self.assertEqual(q.claim(), ("a", 1))
        q.complete("a")
        self.assertFalse(q.submit("a", 3), "completed jobs stay deduplicated")
        with self.assertRaises(KeyError):
            q.complete("a")
        self.assertEqual(q.stats(), {"submitted": 1, "completed": 1, "failed": 1, "dead": 0,
                                     "pending": 0, "running": 0})


if __name__ == "__main__":
    unittest.main()
