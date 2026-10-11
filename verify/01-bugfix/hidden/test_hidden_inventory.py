import unittest

from inventory import add_tag, low_stock, paginate, restock_plan, total_value

ITEMS = [
    {"name": "bolt", "qty": 5, "price": 0.10},
    {"name": "nut", "qty": 3, "price": 0.05},
    {"name": "gear", "qty": 12, "price": 2.50},
]


class Paginate(unittest.TestCase):
    def test_page_one(self):
        self.assertEqual(paginate(list(range(10)), 1, 4), [0, 1, 2, 3])

    def test_page_two(self):
        self.assertEqual(paginate(list(range(10)), 2, 4), [4, 5, 6, 7])

    def test_last_partial_page(self):
        self.assertEqual(paginate(list(range(10)), 3, 4), [8, 9])

    def test_past_end(self):
        self.assertEqual(paginate(list(range(3)), 5, 4), [])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            paginate([1], 0, 4)


class LowStock(unittest.TestCase):
    def test_at_threshold_is_low(self):
        self.assertEqual(low_stock(ITEMS, 5), ["bolt", "nut"])

    def test_below(self):
        self.assertEqual(low_stock(ITEMS, 4), ["nut"])

    def test_none(self):
        self.assertEqual(low_stock(ITEMS, 2), [])


class AddTag(unittest.TestCase):
    def test_tags_do_not_leak_between_calls(self):
        a = add_tag({"name": "a"}, "red")
        b = add_tag({"name": "b"}, "blue")
        self.assertEqual(a["tags"], ["red"])
        self.assertEqual(b["tags"], ["blue"])

    def test_keeps_existing_and_dedupes(self):
        out = add_tag({"name": "a", "tags": ["x"]}, "x")
        self.assertEqual(out["tags"], ["x"])
        out = add_tag({"name": "a", "tags": ["x"]}, "y")
        self.assertEqual(out["tags"], ["x", "y"])

    def test_does_not_mutate_input(self):
        item = {"name": "a", "tags": ["x"]}
        add_tag(item, "y")
        self.assertEqual(item, {"name": "a", "tags": ["x"]})


class Unchanged(unittest.TestCase):
    def test_total_value(self):
        self.assertEqual(total_value(ITEMS), 30.65)

    def test_restock_plan(self):
        self.assertEqual(restock_plan(ITEMS, 6), {"bolt": 1, "nut": 3})


if __name__ == "__main__":
    unittest.main()
