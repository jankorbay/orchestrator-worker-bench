import unittest

from ttlcache import TTLCache


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class StarterTests(unittest.TestCase):
    def test_set_get(self):
        c = TTLCache(2, 10, FakeClock())
        c.set("a", 1)
        self.assertEqual(c.get("a"), 1)

    def test_expiry(self):
        clock = FakeClock()
        c = TTLCache(2, 10, clock)
        c.set("a", 1)
        clock.now = 10
        self.assertIsNone(c.get("a"))


if __name__ == "__main__":
    unittest.main()
