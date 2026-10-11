"""Plain-text invoice rendering (the PDF service uses the same text)."""
from billing.invoice import Invoice
from billing.money import fmt

REVERSE_CHARGE_NOTE = "Reverse charge: VAT to be accounted for by the recipient."


def render(invoice: Invoice) -> str:
    cur = invoice.currency
    out = [f"Invoice {invoice.number}", f"Bill to: {invoice.customer.name} ({invoice.customer.country})"]
    if invoice.customer.vat_id:
        out.append(f"VAT ID: {invoice.customer.vat_id}")
    out.append("")
    for line in invoice.lines:
        out.append(f"{line.qty:>3} x {line.description:<24} {fmt(line.net, cur):>12}  VAT {line.vat_rate}%")
        if line.discount:
            out.append(f"      discount {fmt(-line.discount, cur):>27}")
    out += ["", f"Net   {fmt(invoice.net_total, cur):>12}", f"VAT   {fmt(invoice.vat_total, cur):>12}",
            f"Total {fmt(invoice.total, cur):>12}"]
    if invoice.reverse_charge:
        out.append(REVERSE_CHARGE_NOTE)
    return "\n".join(out)
