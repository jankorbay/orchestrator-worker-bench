import random
import unittest

from shop.fulfilment import ship
from shop.importer import import_orders
from shop.merge import merge
from shop.orders import OrderBook
from shop.reports import availability
from shop.stock import OutOfStock, Stock


def snapshot(book):
    s = book.stock
    return ({k: v for k, v in s.on_hand.items()}, {k: v for k, v in s.reserved.items() if v},
            {i: (o.status, o.customer, [(l.sku, l.qty, l.shipped) for l in o.lines]) for i, o in book.orders.items()})


class Base(unittest.TestCase):
    def setUp(self):
        self.stock = Stock({"MUG-BL": 10, "CAP": 5, "PEN": 3})
        self.book = OrderBook(self.stock)

    def check(self):
        expected = {}
        for o in self.book.orders.values():
            if o.status == "open":
                for l in o.lines:
                    expected[l.sku] = expected.get(l.sku, 0) + l.qty - l.shipped
        actual = {k: v for k, v in self.stock.reserved.items() if v}
        self.assertEqual(actual, {k: v for k, v in expected.items() if v}, "rule 1: reserved == open order lines")
        for sku in set(self.stock.on_hand) | set(self.stock.reserved):
            r, h = self.stock.reserved.get(sku, 0), self.stock.on_hand.get(sku, 0)
            self.assertTrue(0 <= r <= h, f"rule 2 broken for {sku}: reserved={r} on_hand={h}")

    def assertUnchanged(self, exc, fn, *args):
        before = snapshot(self.book)
        with self.assertRaises(exc):
            fn(*args)
        self.assertEqual(snapshot(self.book), before)
        self.check()


class Place(Base):
    def test_failed_order_reserves_nothing(self):
        self.assertUnchanged(OutOfStock, self.book.place, "o1", "ann", [("MUG-BL", 2), ("CAP", 9)])
        self.assertEqual(availability(self.stock), {"MUG-BL": 10, "CAP": 5, "PEN": 3})

    def test_bad_quantity_reserves_nothing(self):
        self.assertUnchanged(ValueError, self.book.place, "o1", "ann", [("MUG-BL", 2), ("CAP", 0)])

    def test_same_sku_twice_cannot_oversell(self):
        self.assertUnchanged(OutOfStock, self.book.place, "o1", "ann", [("MUG-BL", 6), ("MUG-BL", 6)])

    def test_same_sku_twice_fits(self):
        self.book.place("o1", "ann", [("MUG-BL", 6), ("MUG-BL", 4)])
        self.assertEqual(self.stock.available("MUG-BL"), 0)
        self.check()


class Import(Base):
    def rows(self, *orders):
        return [{"order_id": i, "customer": c, "sku": s, "qty": q} for i, c, s, q in orders]

    def test_rejected_order_leaves_no_reservation(self):
        rows = self.rows(("w1", "ann", "MUG-BL", "2"), ("w2", "bob", "MUG-BL", "3"), ("w2", "bob", "CAP", "9"),
                         ("w3", "cat", "PEN", "1"))
        self.assertEqual(import_orders(self.book, rows), ["w2"])
        self.assertEqual(availability(self.stock), {"MUG-BL": 8, "CAP": 5, "PEN": 2})
        self.check()

    def test_bad_row_rolls_back_whole_import(self):
        rows = self.rows(("w1", "ann", "MUG-BL", "2"), ("w2", "bob", "CAP", "1"), ("w3", "cat", "PEN", "zero"))
        self.assertUnchanged(ValueError, import_orders, self.book, rows)

    def test_duplicate_order_rolls_back_whole_import(self):
        self.book.place("w2", "bob", [("PEN", 1)])
        rows = self.rows(("w1", "ann", "MUG-BL", "2"), ("w2", "bob", "CAP", "1"))
        self.assertUnchanged(ValueError, import_orders, self.book, rows)


class Cancel(Base):
    def test_partly_shipped_releases_only_open_part(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.place("b", "bob", [("MUG-BL", 3)])
        ship(self.book, "a", "MUG-BL", 3)
        self.book.cancel("a")
        self.assertEqual(self.stock.reserved["MUG-BL"], 3)
        self.assertEqual(self.stock.available("MUG-BL"), 4)
        self.check()

    def test_cancel_twice_raises(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.place("b", "bob", [("MUG-BL", 3)])
        self.book.cancel("a")
        self.assertUnchanged(ValueError, self.book.cancel, "a")

    def test_cancel_shipped_order_raises(self):
        self.book.place("a", "ann", [("CAP", 2)])
        self.book.place("b", "bob", [("CAP", 3)])
        ship(self.book, "a", "CAP", 2)
        self.assertUnchanged(ValueError, self.book.cancel, "a")


class ChangeQty(Base):
    def test_increase_reserves_only_the_difference(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.change_qty("a", "MUG-BL", 6)
        self.assertEqual(self.stock.reserved["MUG-BL"], 6)
        self.check()

    def test_increase_up_to_all_stock(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.change_qty("a", "MUG-BL", 10)
        self.check()

    def test_increase_beyond_stock_raises(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.place("b", "bob", [("MUG-BL", 4)])
        self.assertUnchanged(OutOfStock, self.book.change_qty, "a", "MUG-BL", 7)

    def test_decrease_releases(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.change_qty("a", "MUG-BL", 1)
        self.assertEqual(self.stock.available("MUG-BL"), 9)
        self.check()

    def test_partly_shipped_line(self):
        self.book.place("a", "ann", [("MUG-BL", 5)])
        ship(self.book, "a", "MUG-BL", 2)
        self.book.change_qty("a", "MUG-BL", 3)
        self.assertEqual(self.stock.reserved["MUG-BL"], 1)
        self.check()


class Ship(Base):
    def test_cancelled_order_cannot_ship(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.place("b", "bob", [("MUG-BL", 3)])
        self.book.cancel("a")
        self.assertUnchanged(ValueError, ship, self.book, "a", "MUG-BL", 2)


class Merge(Base):
    def test_merge_keeps_reservations(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.place("b", "ann", [("MUG-BL", 3), ("CAP", 2)])
        merge(self.book, "a", "b")
        self.assertEqual(self.book.orders["a"].status, "open")
        self.assertEqual(self.book.orders["b"].status, "cancelled")
        self.assertEqual(self.stock.available("MUG-BL"), 3)
        self.assertEqual(self.stock.available("CAP"), 3)
        self.check()

    def test_no_oversell_after_merge(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.place("b", "ann", [("MUG-BL", 6)])
        merge(self.book, "a", "b")
        self.assertUnchanged(OutOfStock, self.book.place, "c", "cat", [("MUG-BL", 1)])

    def test_merge_partly_shipped(self):
        self.book.place("a", "ann", [("MUG-BL", 4)])
        self.book.place("b", "ann", [("MUG-BL", 3), ("PEN", 2)])
        ship(self.book, "b", "MUG-BL", 2)
        merge(self.book, "a", "b")
        self.assertEqual(self.stock.reserved["MUG-BL"], 5)
        self.check()
        ship(self.book, "a", "MUG-BL", 5)
        ship(self.book, "a", "PEN", 2)
        self.assertEqual(self.book.orders["a"].status, "shipped")
        self.check()


class RandomOperations(Base):
    """Random mixes of every operation; the rules must hold after each step."""

    def run_ops(self, seed, n=400):
        rnd = random.Random(seed)
        skus = ["MUG-BL", "CAP", "PEN"]
        customers = ["ann", "bob"]
        next_id = 0
        for _ in range(n):
            ids = list(self.book.orders)
            op = rnd.choice(["place", "place", "cancel", "change", "ship", "ship", "merge", "receive", "import"])
            before = snapshot(self.book)
            try:
                if op == "place":
                    next_id += 1
                    items = [(rnd.choice(skus), rnd.randint(1, 4)) for _ in range(rnd.randint(1, 3))]
                    self.book.place(f"o{next_id}", rnd.choice(customers), items)
                elif op == "import":
                    rows = []
                    for _ in range(rnd.randint(1, 3)):
                        next_id += 1
                        c = rnd.choice(customers)
                        for _ in range(rnd.randint(1, 2)):
                            rows.append({"order_id": f"o{next_id}", "customer": c, "sku": rnd.choice(skus),
                                         "qty": rnd.choice(["1", "2", "3", "0"] if rnd.random() < 0.2 else ["1", "2"])})
                    import_orders(self.book, rows)
                elif op == "receive":
                    self.stock.receive(rnd.choice(skus), rnd.randint(1, 3))
                elif ids:
                    o = self.book.orders[rnd.choice(ids)]
                    line = rnd.choice(o.lines)
                    if op == "cancel":
                        self.book.cancel(o.id)
                    elif op == "change":
                        self.book.change_qty(o.id, line.sku, rnd.randint(1, 6))
                    elif op == "ship":
                        ship(self.book, o.id, line.sku, rnd.randint(1, 3))
                    elif op == "merge":
                        merge(self.book, o.id, rnd.choice(ids))
            except (OutOfStock, ValueError, KeyError):
                self.assertEqual(snapshot(self.book), before, f"seed {seed}: failed {op} changed state")
            self.check()

    def test_random_1(self):
        self.run_ops(1)

    def test_random_2(self):
        self.run_ops(2)

    def test_random_3(self):
        self.run_ops(3)


if __name__ == "__main__":
    unittest.main()
