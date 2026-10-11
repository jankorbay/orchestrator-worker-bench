"""Credit notes: refund some lines of an issued invoice."""
from dataclasses import replace

from billing.invoice import Invoice


def credit_note(number: str, invoice: Invoice, skus: set[str]) -> Invoice:
    """A credit note refunding the given SKUs exactly as they were invoiced."""
    refunded = [replace(line, discount=-line.discount, net=-line.net, vat=-line.vat, gross=-line.gross)
                for line in invoice.lines if line.sku in skus]
    if not refunded:
        raise ValueError("no matching lines to refund")
    return Invoice(number, invoice.customer, invoice.currency, refunded, invoice.reverse_charge, invoice.code)
