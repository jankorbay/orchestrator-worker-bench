import unittest

from ttlcache import TTLCache


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def make(cap=2, ttl=10):
    clock = FakeClock()
    return TTLCache(cap, ttl, clock), clock


class Basics(unittest.TestCase):
    def test_invalid_args(self):
        for cap, ttl in ((0, 1), (-1, 1), (1, 0), (1, -5)):
            with self.assertRaises(ValueError):
                TTLCache(cap, ttl, FakeClock())

    def test_default(self):
        c, _ = make()
        self.assertEqual(c.get("x", "d"), "d")

    def test_overwrite(self):
        c, _ = make()
        c.set("a", 1)
        c.set("a", 2)
        self.assertEqual(c.get("a"), 2)
        self.assertEqual(len(c), 1)


class Expiry(unittest.TestCase):
    def test_boundary(self):
        c, clock = make()
        c.set("a", 1)
        clock.now += 9.999
        self.assertEqual(c.get("a"), 1)
        clock.now += 0.001
        self.assertIsNone(c.get("a"))

    def test_get_does_not_extend_ttl(self):
        c, clock = make()
        c.set("a", 1)
        clock.now += 6
        c.get("a")
        clock.now += 6
        self.assertNotIn("a", c)

    def test_overwrite_resets_ttl(self):
        c, clock = make()
        c.set("a", 1)
        clock.now += 6
        c.set("a", 2)
        clock.now += 6
        self.assertEqual(c.get("a"), 2)

    def test_len_and_contains_ignore_expired(self):
        c, clock = make()
        c.set("a", 1)
        clock.now += 5
        c.set("b", 2)
        clock.now += 5
        self.assertEqual(len(c), 1)
        self.assertNotIn("a", c)
        self.assertIn("b", c)

    def test_delete(self):
        c, clock = make()
        c.set("a", 1)
        c.set("b", 2)
        self.assertTrue(c.delete("a"))
        self.assertFalse(c.delete("a"))
        clock.now += 10
        self.assertFalse(c.delete("b"))


class Eviction(unittest.TestCase):
    def test_lru_evicted(self):
        c, _ = make()
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)
        self.assertNotIn("a", c)
        self.assertEqual(c.stats()["evictions"], 1)

    def test_get_refreshes_recency(self):
        c, _ = make()
        c.set("a", 1)
        c.set("b", 2)
        c.get("a")
        c.set("c", 3)
        self.assertIn("a", c)
        self.assertNotIn("b", c)

    def test_contains_does_not_refresh_recency(self):
        c, _ = make()
        c.set("a", 1)
        c.set("b", 2)
        self.assertIn("a", c)
        c.set("c", 3)
        self.assertNotIn("a", c)

    def test_overwrite_refreshes_recency_without_eviction(self):
        c, _ = make()
        c.set("a", 1)
        c.set("b", 2)
        c.set("a", 9)
        self.assertEqual(c.stats()["evictions"], 0)
        c.set("c", 3)
        self.assertIn("a", c)
        self.assertNotIn("b", c)

    def test_expired_dropped_before_lru_eviction(self):
        c, clock = make(cap=2, ttl=10)
        c.set("old", 1)
        clock.now += 5
        c.set("fresh", 2)
        clock.now += 6  # "old" expired, "fresh" still live
        c.set("new", 3)
        self.assertIn("fresh", c)
        self.assertIn("new", c)
        self.assertEqual(c.stats()["evictions"], 0)


class Stats(unittest.TestCase):
    def test_hits_and_misses(self):
        c, clock = make()
        c.set("a", 1)
        c.get("a")
        c.get("a")
        c.get("zzz")
        clock.now += 10
        c.get("a")
        self.assertEqual(c.stats(), {"hits": 2, "misses": 2, "evictions": 0})


if __name__ == "__main__":
    unittest.main()
