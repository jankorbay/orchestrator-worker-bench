import unittest

from shop.fulfilment import ship
from shop.importer import import_orders
from shop.orders import OrderBook
from shop.reports import availability
from shop.stock import OutOfStock, Stock


class Flows(unittest.TestCase):
    def setUp(self):
        self.stock = Stock({"MUG": 10, "CAP": 5})
        self.book = OrderBook(self.stock)

    def test_place_reserves(self):
        self.book.place("o1", "ann", [("MUG", 3), ("CAP", 1)])
        self.assertEqual(availability(self.stock), {"MUG": 7, "CAP": 4})

    def test_out_of_stock(self):
        with self.assertRaises(OutOfStock):
            self.book.place("o1", "ann", [("CAP", 6)])
        self.assertEqual(self.book.orders, {})

    def test_cancel_releases(self):
        self.book.place("o1", "ann", [("MUG", 3)])
        self.book.cancel("o1")
        self.assertEqual(availability(self.stock)["MUG"], 10)

    def test_ship_everything(self):
        self.book.place("o1", "ann", [("MUG", 3)])
        ship(self.book, "o1", "MUG", 3)
        self.assertEqual(self.book.orders["o1"].status, "shipped")
        self.assertEqual((self.stock.on_hand["MUG"], self.stock.reserved["MUG"]), (7, 0))

    def test_import(self):
        rows = [{"order_id": "w1", "customer": "ann", "sku": "MUG", "qty": "2"},
                {"order_id": "w2", "customer": "bob", "sku": "CAP", "qty": "9"}]
        self.assertEqual(import_orders(self.book, rows), ["w2"])
        self.assertEqual(availability(self.stock), {"MUG": 8, "CAP": 5})


if __name__ == "__main__":
    unittest.main()
