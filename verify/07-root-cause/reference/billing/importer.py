"""Import a web-shop order export (CSV, one row per line item) into an invoice."""
import csv
import io
from decimal import Decimal

from billing.customers import Customer
from billing.invoice import Invoice, Line, build_invoice

COLUMNS = ["customer", "country", "currency", "vat_id", "sku", "description",
           "qty", "unit_price_eur", "category", "code"]


def parse_order(text: str) -> tuple[Customer, list[Line], str | None]:
    rows = list(csv.DictReader(io.StringIO(text.strip())))
    if not rows:
        raise ValueError("empty order")
    missing = set(COLUMNS) - set(rows[0])
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    first = rows[0]
    customer = Customer(first["customer"], first["country"], first["currency"], first["vat_id"] or None)
    lines = [Line(r["sku"], r["description"], int(r["qty"]), Decimal(r["unit_price_eur"]),
                  r["category"] or "general") for r in rows]
    return customer, lines, first["code"] or None


def import_order(number: str, text: str) -> Invoice:
    customer, lines, code = parse_order(text)
    return build_invoice(number, customer, lines, code)
