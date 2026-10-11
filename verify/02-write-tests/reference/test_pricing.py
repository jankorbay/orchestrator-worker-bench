import unittest
from decimal import Decimal

from pricing import price_order, validate_line


def line(qty, price, sku="A"):
    return {"sku": sku, "qty": qty, "unit_price": price}


class Validation(unittest.TestCase):
    def test_rejects(self):
        for bad in (line(0, "1"), line(-1, "1"), line(1, "-0.01"), line(1, "1", sku="")):
            with self.assertRaises(ValueError):
                validate_line(bad)

    def test_accepts_free_item(self):
        validate_line(line(1, "0"))


class Pricing(unittest.TestCase):
    def test_bulk_boundary(self):
        self.assertEqual(price_order([line(9, "1")]), Decimal("9.00"))
        self.assertEqual(price_order([line(10, "1")]), Decimal("9.00"))

    def test_save5_boundary(self):
        self.assertEqual(price_order([line(1, "50")], "SAVE5"), Decimal("45.00"))
        self.assertEqual(price_order([line(1, "49.99")], "SAVE5"), Decimal("49.99"))

    def test_coupon_case_insensitive(self):
        self.assertEqual(price_order([line(1, "60")], "save5"), Decimal("55.00"))

    def test_unknown_coupon(self):
        with self.assertRaises(ValueError):
            price_order([line(1, "60")], "BOGUS")

    def test_tenoff_small_order(self):
        self.assertEqual(price_order([line(1, "20")], "TENOFF"), Decimal("18.00"))

    def test_member_after_coupon(self):
        self.assertEqual(price_order([line(1, "100")], "SAVE5", member=True), Decimal("90.25"))

    def test_half_up_rounding(self):
        self.assertEqual(price_order([line(1, "0.125")]), Decimal("0.13"))


if __name__ == "__main__":
    unittest.main()
