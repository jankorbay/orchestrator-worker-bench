"""Monthly VAT report for the tax advisor."""
from collections import defaultdict
from decimal import Decimal

from billing.invoice import Invoice
from billing.rates import convert


def vat_by_country(invoices: list[Invoice]) -> dict[str, Decimal]:
    """VAT charged per customer country, in EUR, rounded to cents."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for inv in invoices:
        totals[inv.customer.country] += convert(inv.vat_total, inv.currency, "EUR")
    return {country: amount.quantize(Decimal("0.01")) for country, amount in sorted(totals.items())}


def reverse_charge_customers(invoices: list[Invoice]) -> list[str]:
    """Names of customers invoiced under reverse charge (for the EC sales list)."""
    return sorted({inv.customer.name for inv in invoices if inv.reverse_charge})
