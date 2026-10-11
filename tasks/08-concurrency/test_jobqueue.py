import unittest

from jobqueue import JobQueue, run_workers


class SingleThreaded(unittest.TestCase):
    def test_fifo_and_dedupe(self):
        q = JobQueue()
        self.assertTrue(q.submit("a", 1))
        self.assertTrue(q.submit("b", 2))
        self.assertFalse(q.submit("a", 9))
        self.assertEqual(q.claim(), ("a", 1))
        self.assertEqual(q.claim(), ("b", 2))
        self.assertIsNone(q.claim())

    def test_retry_then_dead(self):
        q = JobQueue(max_attempts=2)
        q.submit("a", 1)
        q.claim()
        q.fail("a")
        q.claim()
        q.fail("a")
        self.assertEqual(q.dead_jobs(), {"a"})
        self.assertEqual(q.stats(), {"submitted": 1, "completed": 0, "failed": 2, "dead": 1,
                                     "pending": 0, "running": 0})


class Workers(unittest.TestCase):
    def test_processes_everything(self):
        q = JobQueue()
        for i in range(50):
            q.submit(i, i)
        seen = []
        run_workers(q, lambda job_id, payload: seen.append(job_id), n_workers=2)
        self.assertEqual(sorted(seen), list(range(50)))


if __name__ == "__main__":
    unittest.main()
