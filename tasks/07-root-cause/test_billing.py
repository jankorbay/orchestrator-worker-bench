import unittest
from decimal import Decimal as D

from billing.customers import Customer
from billing.invoice import Line, build_invoice
from billing.render import render


class BillingTests(unittest.TestCase):
    def test_german_consumer(self):
        inv = build_invoice("T1", Customer("Anna", "DE", "EUR"), [Line("BK-1", "Book", 2, D("10.00"), "books")])
        self.assertEqual((inv.net_total, inv.vat_total, inv.total), (D("20.00"), D("1.40"), D("21.40")))

    def test_percent_code(self):
        inv = build_invoice("T2", Customer("Anna", "DE", "EUR"), [Line("X", "Thing", 1, D("50.00"))], "spring10")
        self.assertEqual(inv.lines[0].net, D("45.00"))

    def test_export_has_no_vat(self):
        inv = build_invoice("T3", Customer("Acme Inc", "US", "USD"), [Line("X", "Thing", 1, D("10.00"))])
        self.assertEqual((inv.total, inv.vat_total), (D("10.92"), D("0")))

    def test_render(self):
        inv = build_invoice("T4", Customer("Anna", "DE", "EUR"), [Line("X", "Thing", 1, D("10.00"))])
        self.assertIn("Total       €11.90", render(inv))


if __name__ == "__main__":
    unittest.main()
