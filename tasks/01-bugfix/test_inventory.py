import unittest

from inventory import paginate, total_value


class VisibleTests(unittest.TestCase):
    def test_first_page(self):
        self.assertEqual(paginate(list(range(10)), 1, 3), [0, 1, 2])

    def test_total_value(self):
        self.assertEqual(total_value([{"qty": 2, "price": 1.5}]), 3.0)


if __name__ == "__main__":
    unittest.main()
