import unittest
from datetime import datetime as dt

from cron import next_run


class Fields(unittest.TestCase):
    def test_step_star(self):
        self.assertEqual(next_run("*/15 * * * *", dt(2026, 1, 1, 10, 46)), dt(2026, 1, 1, 11, 0))

    def test_step_range(self):
        self.assertEqual(next_run("5-20/5 * * * *", dt(2026, 1, 1, 10, 21)), dt(2026, 1, 1, 11, 5))

    def test_step_from_single_value(self):
        self.assertEqual(next_run("10/20 * * * *", dt(2026, 1, 1, 10, 31)), dt(2026, 1, 1, 10, 50))
        self.assertEqual(next_run("10/20 * * * *", dt(2026, 1, 1, 10, 51)), dt(2026, 1, 1, 11, 10))

    def test_list(self):
        self.assertEqual(next_run("0 9,17 * * *", dt(2026, 1, 1, 12, 0)), dt(2026, 1, 1, 17, 0))

    def test_strictly_after(self):
        self.assertEqual(next_run("30 10 * * *", dt(2026, 1, 1, 10, 30)), dt(2026, 1, 2, 10, 30))

    def test_sub_minute_input(self):
        self.assertEqual(next_run("* * * * *", dt(2026, 1, 1, 10, 0, 59, 999999)),
                         dt(2026, 1, 1, 10, 1))

    def test_midnight_rollover(self):
        self.assertEqual(next_run("59 23 * * *", dt(2026, 1, 1, 23, 59)), dt(2026, 1, 2, 23, 59))


class Calendar(unittest.TestCase):
    def test_month_rollover(self):
        self.assertEqual(next_run("0 0 1 * *", dt(2026, 1, 31, 12, 0)), dt(2026, 2, 1))

    def test_skips_short_months(self):
        self.assertEqual(next_run("0 0 31 * *", dt(2026, 1, 31, 1, 0)), dt(2026, 3, 31))

    def test_leap_day(self):
        self.assertEqual(next_run("0 0 29 2 *", dt(2025, 3, 1)), dt(2028, 2, 29))

    def test_year_rollover(self):
        self.assertEqual(next_run("0 0 1 1 *", dt(2026, 12, 31, 23, 59)), dt(2027, 1, 1))

    def test_month_field(self):
        self.assertEqual(next_run("0 0 * 2 *", dt(2026, 10, 9)), dt(2027, 2, 1))


class DayOfWeek(unittest.TestCase):
    # 2026-10-09 is a Friday.
    def test_monday(self):
        self.assertEqual(next_run("0 12 * * 1", dt(2026, 10, 9)), dt(2026, 10, 12, 12, 0))

    def test_sunday_is_0_and_7(self):
        self.assertEqual(next_run("0 8 * * 7", dt(2026, 10, 9)), dt(2026, 10, 11, 8, 0))
        self.assertEqual(next_run("0 8 * * 0", dt(2026, 10, 9)), dt(2026, 10, 11, 8, 0))

    def test_range_ending_at_7(self):
        self.assertEqual(next_run("0 9 * * 5-7", dt(2026, 10, 10, 10, 0)), dt(2026, 10, 11, 9, 0))

    def test_dom_or_dow_when_both_restricted(self):
        self.assertEqual(next_run("0 0 13 * 5", dt(2026, 10, 9)), dt(2026, 10, 13))

    def test_dom_and_dow_when_dow_starts_with_star(self):
        # 1st of a month that is also Sun/Tue/Thu/Sat; Oct 10 (Sat) must not match.
        self.assertEqual(next_run("0 0 1 * */2", dt(2026, 10, 9)), dt(2026, 11, 1))


class Errors(unittest.TestCase):
    def test_malformed(self):
        for expr in ("60 * * * *", "* 24 * * *", "* * 0 * *", "* * * 13 *", "* * * * 8",
                     "* * * *", "* * * * * *", "*/0 * * * *", "5-1 * * * *", "a * * * *",
                     "1,,2 * * * *", "-1 * * * *"):
            with self.subTest(expr=expr), self.assertRaises(ValueError):
                next_run(expr, dt(2026, 1, 1))

    def test_never_matches(self):
        for expr in ("0 0 30 2 *", "0 0 31 4 *"):
            with self.subTest(expr=expr), self.assertRaises(ValueError):
                next_run(expr, dt(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
