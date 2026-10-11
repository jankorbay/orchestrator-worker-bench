"""FX rates, fixed daily by finance. A rate is units of the currency per 1 EUR."""
from decimal import Decimal

RATES = {
    "EUR": Decimal("1"),
    "GBP": Decimal("0.8550"),
    "USD": Decimal("1.0920"),
    "CHF": Decimal("0.9410"),
}


def convert(amount: Decimal, src: str, dst: str) -> Decimal:
    """Convert between currencies without rounding. Callers round where the rules say."""
    if src not in RATES or dst not in RATES:
        raise ValueError(f"unsupported currency pair {src}->{dst}")
    return amount / RATES[src] * RATES[dst]
