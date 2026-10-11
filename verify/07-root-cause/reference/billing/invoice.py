"""Invoice calculation. The rules are in BILLING_RULES.md."""
from dataclasses import dataclass
from decimal import Decimal

from billing import discounts, tax
from billing.customers import Customer
from billing.money import round_cents
from billing.rates import convert


@dataclass
class Line:
    sku: str
    description: str
    qty: int
    unit_price_eur: Decimal  # catalog prices are always in EUR
    category: str = "general"


@dataclass
class InvoiceLine:
    sku: str
    description: str
    qty: int
    discount: Decimal  # invoice currency
    net: Decimal  # after discount, invoice currency
    vat_rate: Decimal  # percent
    vat: Decimal
    gross: Decimal


@dataclass
class Invoice:
    number: str
    customer: Customer
    currency: str
    lines: list[InvoiceLine]
    reverse_charge: bool
    code: str | None = None

    @property
    def net_total(self) -> Decimal:
        return sum((line.net for line in self.lines), Decimal(0))

    @property
    def vat_total(self) -> Decimal:
        return sum((line.vat for line in self.lines), Decimal(0))

    @property
    def total(self) -> Decimal:
        return sum((line.gross for line in self.lines), Decimal(0))


def line_discounts(code: discounts.Code | None, lines: list[Line], nets: list[Decimal],
                   currency: str) -> list[Decimal]:
    """Discount per line in the invoice currency."""
    none = [Decimal(0)] * len(lines)
    if code is None:
        return none
    order_eur = sum((line.qty * line.unit_price_eur for line in lines), Decimal(0))
    if order_eur < code.min_order_eur:
        return none
    if code.kind == "percent":
        return [round_cents(net * code.value / 100) if code.category in (None, line.category)
                else Decimal(0) for line, net in zip(lines, nets)]
    return discounts.allocate_fixed(round_cents(convert(code.value, "EUR", currency)), nets)


def build_invoice(number: str, customer: Customer, lines: list[Line],
                  code: str | None = None) -> Invoice:
    if not lines:
        raise ValueError("an invoice needs at least one line")
    currency = customer.currency
    nets = [round_cents(convert(line.qty * line.unit_price_eur, "EUR", currency)) for line in lines]
    discount_by_line = line_discounts(discounts.lookup(code), lines, nets, currency)

    out = []
    for line, gross_net, discount in zip(lines, nets, discount_by_line):
        net = gross_net - discount
        rate = tax.vat_rate(customer, line.category)
        vat = round_cents(net * rate / 100)
        out.append(InvoiceLine(line.sku, line.description, line.qty, discount, net, rate, vat, net + vat))
    return Invoice(number, customer, currency, out, tax.is_reverse_charge(customer), code)
