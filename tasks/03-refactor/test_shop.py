import unittest

from shop.cart import Cart
from shop.money import fmt_money, parse_money
from shop.receipt import render_receipt
from shop.report import daily_report


class ShopTests(unittest.TestCase):
    def test_money_roundtrip(self):
        self.assertEqual(fmt_money(123456), "$1,234.56")
        self.assertEqual(parse_money("$1,234.56"), 123456)

    def test_cart(self):
        cart = Cart()
        cart.add("tea", 250, 2)
        self.assertEqual(cart.summary(), "1 item(s), total $5.00")
        self.assertIn("TOTAL", render_receipt(cart))

    def test_report(self):
        self.assertEqual(daily_report([500, 20000])["total"], "$205.00")


if __name__ == "__main__":
    unittest.main()
