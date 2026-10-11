"""Discount codes. See BILLING_RULES.md for how they apply."""
from dataclasses import dataclass
from decimal import Decimal

from billing.money import round_cents


@dataclass(frozen=True)
class Code:
    kind: str  # "percent" or "fixed"
    value: Decimal  # percent, or an amount in EUR for fixed codes
    category: str | None = None  # percent codes only: restrict to one category
    min_order_eur: Decimal = Decimal(0)


CODES = {
    "SPRING10": Code("percent", Decimal(10)),
    "BOOKS15": Code("percent", Decimal(15), category="books"),
    "WELCOME20": Code("fixed", Decimal(20), min_order_eur=Decimal(50)),
    "LOYAL50": Code("fixed", Decimal(50), min_order_eur=Decimal(200)),
}


def lookup(code: str | None) -> Code | None:
    if code is None or not code.strip():
        return None
    try:
        return CODES[code.strip().upper()]
    except KeyError:
        raise ValueError(f"unknown discount code {code!r}") from None


def allocate_fixed(amount: Decimal, nets: list[Decimal]) -> list[Decimal]:
    """Split a fixed discount over lines in proportion to their net amounts.

    Shares are rounded to cents and the rounding remainder is put on one line so the
    shares add up exactly to `amount`. The discount never exceeds the order's net total.
    """
    total = sum(nets, Decimal(0))
    if total <= 0:
        return [Decimal(0)] * len(nets)
    amount = min(amount, total)
    shares = [round_cents(amount * net / total) for net in nets]
    shares[0] += amount - sum(shares, Decimal(0))
    return shares
