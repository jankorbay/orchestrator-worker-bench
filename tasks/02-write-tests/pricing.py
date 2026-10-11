"""Order pricing for the web shop.

Rules:
1. A line is {"sku": str, "qty": int, "unit_price": str | int | Decimal}.
   validate_line raises ValueError if sku is empty, qty <= 0, or unit_price < 0.
2. Line total = qty * unit_price. A line with qty >= 10 gets 10% off that line only.
3. Subtotal = sum of all line totals.
4. Coupon (case-insensitive): None, "SAVE5" ($5 off, only when subtotal >= 50)
   or "TENOFF" (10% off, any subtotal). Any other code raises ValueError.
5. Members get 5% off, applied after the coupon.
6. The result is a Decimal rounded to cents, half-up (0.125 -> 0.13).
"""
from decimal import ROUND_HALF_UP, Decimal

COUPONS = {"SAVE5", "TENOFF"}


def validate_line(line: dict) -> None:
    if not line.get("sku"):
        raise ValueError("sku is required")
    if line["qty"] <= 0:
        raise ValueError("qty must be positive")
    if Decimal(str(line["unit_price"])) < 0:
        raise ValueError("unit_price must not be negative")


def line_total(line: dict) -> Decimal:
    validate_line(line)
    total = line["qty"] * Decimal(str(line["unit_price"]))
    if line["qty"] >= 10:
        total *= Decimal("0.9")
    return total


def price_order(lines: list[dict], coupon: str | None = None, member: bool = False) -> Decimal:
    subtotal = sum((line_total(line) for line in lines), Decimal(0))
    if coupon is not None:
        code = coupon.upper()
        if code not in COUPONS:
            raise ValueError(f"unknown coupon {coupon!r}")
        if code == "SAVE5" and subtotal >= 50:
            subtotal -= 5
        elif code == "TENOFF":
            subtotal *= Decimal("0.9")
    if member:
        subtotal *= Decimal("0.95")
    return subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
