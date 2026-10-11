"""Money helpers. All amounts are Decimal; never use float for money."""
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
SYMBOLS = {"EUR": "€", "GBP": "£", "USD": "$", "CHF": "CHF "}


def D(value) -> Decimal:
    """Decimal from int, str or Decimal. Floats are rejected because they are not exact."""
    if isinstance(value, float):
        raise TypeError("use str or Decimal for money, not float")
    return Decimal(value)


def round_cents(amount: Decimal) -> Decimal:
    """Round to cents, half up (finance policy)."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def fmt(amount: Decimal, currency: str) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}{SYMBOLS.get(currency, currency + ' ')}{abs(round_cents(amount)):,.2f}"
