import unittest
from datetime import datetime

from cron import next_run


class StarterTests(unittest.TestCase):
    def test_every_minute(self):
        self.assertEqual(next_run("* * * * *", datetime(2026, 1, 1, 10, 0, 30)),
                         datetime(2026, 1, 1, 10, 1))

    def test_daily(self):
        self.assertEqual(next_run("30 6 * * *", datetime(2026, 1, 1, 7, 0)),
                         datetime(2026, 1, 2, 6, 30))


if __name__ == "__main__":
    unittest.main()
