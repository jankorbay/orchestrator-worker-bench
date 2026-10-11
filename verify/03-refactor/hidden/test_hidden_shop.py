import unittest

from shop.cart import Cart
from shop.money import format_money, parse_money
from shop.receipt import render_line, render_receipt
from shop.report import daily_report


class Money(unittest.TestCase):
    def test_format(self):
        self.assertEqual(format_money(123456), "$1,234.56")
        self.assertEqual(format_money(-5, "EUR"), "-€0.05")
        self.assertEqual(format_money(100, "CHF"), "CHF 1.00")

    def test_parse(self):
        self.assertEqual(parse_money(" -1,000.5 "), -100050)
        self.assertEqual(parse_money("7"), 700)


class CartAndReceipt(unittest.TestCase):
    def test_cart(self):
        cart = Cart("GBP")
        cart.add("tea", 250, 2)
        cart.add("cake", 399)
        self.assertEqual(cart.total(), 899)
        self.assertEqual(cart.summary(), "2 item(s), total £8.99")
        with self.assertRaises(ValueError):
            cart.add("x", 1, 0)

    def test_receipt(self):
        cart = Cart()
        cart.add("tea", 250, 2)
        self.assertEqual(render_line("tea", 250, 2), "2 x tea                 $5.00")
        self.assertEqual(render_receipt(cart).splitlines()[-1], "TOTAL                   $5.00")


class Report(unittest.TestCase):
    def test_report(self):
        r = daily_report([500, 20000, 1500])
        self.assertEqual(r, {"count": 3, "total": "$220.00", "average": "$73.33",
                             "by_size": {"small": 2, "large": 1}})

    def test_empty(self):
        self.assertEqual(daily_report([])["average"], "$0.00")


if __name__ == "__main__":
    unittest.main()
