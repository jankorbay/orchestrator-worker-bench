import unittest
from decimal import Decimal as D

from billing.credit_note import credit_note
from billing.customers import Customer
from billing.discounts import allocate_fixed
from billing.importer import import_order
from billing.invoice import Line, build_invoice
from billing.render import REVERSE_CHARGE_NOTE, render
from billing.reports import reverse_charge_customers


def brightside():
    lines = [Line("KB-01", "Mechanical keyboard", 1, D("28.21")), Line("MS-02", "Wireless mouse", 3, D("11.19")),
             Line("HS-03", "USB headset", 1, D("26.97"))]
    return build_invoice("2026-0412", Customer("Brightside Ltd", "GB", "GBP"), lines, "WELCOME20")


def lines_of(inv):
    return [(line.sku, line.discount, line.net) for line in inv.lines]


class ReportedComplaints(unittest.TestCase):
    def test_complaint_1_brightside(self):
        inv = brightside()
        self.assertEqual(lines_of(inv), [("KB-01", D("5.44"), D("18.68")), ("MS-02", D("6.46"), D("22.24")),
                                         ("HS-03", D("5.20"), D("17.86"))])
        self.assertEqual(inv.total, D("58.78"))

    def test_complaint_2_mueller(self):
        m = Customer("Müller Technik GmbH", "AT", "EUR", "atu-1234.5678")
        inv = build_invoice("2026-0419", m, [Line("MON-27", '27" monitor', 2, D("219.00"))])
        self.assertEqual(m.vat_id, "ATU12345678")
        self.assertTrue(inv.reverse_charge)
        self.assertEqual((inv.vat_total, inv.total), (D("0"), D("438.00")))
        self.assertIn(REVERSE_CHARGE_NOTE, render(inv))


class FixedCodesInOtherCurrencies(unittest.TestCase):
    def test_usd_welcome20(self):
        inv = build_invoice("U", Customer("Acme Inc", "US", "USD"),
                            [Line("A", "A", 2, D("15.00")), Line("B", "B", 1, D("40.00"))], "WELCOME20")
        self.assertEqual([line.discount for line in inv.lines], [D("9.36"), D("12.48")])
        self.assertEqual(inv.total, D("54.60"))

    def test_chf_loyal50(self):
        inv = build_invoice("C", Customer("Alpen AG", "CH", "CHF"),
                            [Line("A", "A", 4, D("55.00")), Line("B", "B", 1, D("30.00"))], "LOYAL50")
        self.assertEqual([line.discount for line in inv.lines], [D("41.40"), D("5.65")])
        self.assertEqual(inv.total, D("188.20"))

    def test_minimum_order_is_checked_in_eur(self):
        inv = build_invoice("M", Customer("Brightside Ltd", "GB", "GBP"), [Line("A", "A", 1, D("49.99"))], "WELCOME20")
        self.assertEqual(inv.lines[0].discount, D("0"))


class RemainderAllocation(unittest.TestCase):
    def test_remainder_goes_to_largest_line_before_vat(self):
        lines = [Line("S0", "Item 0", 1, D("26.42")), Line("S1", "Item 1", 1, D("20.97")),
                 Line("S2", "Item 2", 1, D("35.36"))]
        inv = build_invoice("E", Customer("Anna", "DE", "EUR"), lines, "WELCOME20")
        self.assertEqual([(line.discount, line.net, line.vat) for line in inv.lines],
                         [(D("6.39"), D("20.03"), D("3.81")), (D("5.07"), D("15.90"), D("3.02")),
                          (D("8.54"), D("26.82"), D("5.10"))])
        self.assertEqual(inv.total, D("74.68"))

    def test_tie_goes_to_first_largest(self):
        self.assertEqual(allocate_fixed(D("6.94"), [D("5.85"), D("16.40"), D("16.40")]),
                         [D("1.05"), D("2.95"), D("2.94")])

    def test_shares_add_up(self):
        shares = allocate_fixed(D("10.00"), [D("3.33"), D("3.33"), D("3.34")])
        self.assertEqual(sum(shares), D("10.00"))


class CreditNotes(unittest.TestCase):
    def test_refund_matches_invoiced_line(self):
        note = credit_note("CN-1", brightside(), {"MS-02"})
        self.assertEqual(lines_of(note), [("MS-02", D("-6.46"), D("-22.24"))])
        self.assertEqual(note.total, D("-22.24"))


ORDER = """customer,country,currency,vat_id,sku,description,qty,unit_price_eur,category,code
{name},{country},EUR,{vat},X1,Widget,2,100.00,,
"""


class VatIdsFromTheWebShop(unittest.TestCase):
    def check(self, name, country, raw, canonical, reverse):
        inv = import_order("W", ORDER.format(name=name, country=country, vat=raw))
        self.assertEqual(inv.customer.vat_id, canonical)
        self.assertEqual(inv.reverse_charge, reverse)
        return inv

    def test_belgian_with_dots(self):
        self.check("Gent BV", "BE", "be 0123.456.789", "BE0123456789", True)

    def test_dutch_with_dashes(self):
        self.check("Delft BV", "NL", "nl-123456789-b01", "NL123456789B01", True)

    def test_spanish_lowercase_letters(self):
        self.check("Sevilla SL", "ES", "es x1234567z", "ESX1234567Z", True)

    def test_german_business_pays_german_vat(self):
        inv = self.check("Köln GmbH", "DE", "de 811.907.980", "DE811907980", False)
        self.assertEqual(inv.vat_total, D("38.00"))

    def test_malformed_id_pays_vat(self):
        inv = self.check("Graz GmbH", "AT", "ATU 1234567", "ATU1234567", False)
        self.assertEqual(inv.vat_total, D("40.00"))

    def test_ec_sales_list(self):
        inv = import_order("W", ORDER.format(name="Delft BV", country="NL", vat="nl 123456789 b01"))
        self.assertEqual(reverse_charge_customers([inv]), ["Delft BV"])


class Unchanged(unittest.TestCase):
    def test_books_code_only_on_books(self):
        lines = [Line("BK", "Book", 1, D("20.00"), "books"), Line("PN", "Pen", 1, D("10.00"))]
        inv = build_invoice("B", Customer("Anna", "DE", "EUR"), lines, "BOOKS15")
        self.assertEqual([(line.discount, line.vat) for line in inv.lines], [(D("3.00"), D("1.19")), (D("0"), D("1.90"))])

    def test_no_code(self):
        inv = build_invoice("N", Customer("Brightside Ltd", "GB", "GBP"), [Line("A", "A", 2, D("10.00"))])
        self.assertEqual(inv.total, D("17.10"))


if __name__ == "__main__":
    unittest.main()
