"""Seeded bugs for task 02: (name, old text, new text), applied to the original pricing.py."""

MUTANTS = [
    ("bulk_threshold", 'if line["qty"] >= 10:', 'if line["qty"] > 10:'),
    ("save5_threshold", "subtotal >= 50:", "subtotal > 50:"),
    ("coupon_case", "code = coupon.upper()", "code = coupon"),
    ("zero_qty_allowed", 'line["qty"] <= 0:', 'line["qty"] < 0:'),
    ("negative_price_allowed", '["unit_price"])) < 0:', '["unit_price"])) < -100:'),
    ("bankers_rounding", "rounding=ROUND_HALF_UP", 'rounding="ROUND_HALF_EVEN"'),
    ("unknown_coupon_ignored", "if code not in COUPONS:", "if False:"),
    ("tenoff_needs_50", 'elif code == "TENOFF":', 'elif code == "TENOFF" and subtotal >= 50:'),
]


def apply(src: str, old: str, new: str) -> str:
    assert src.count(old) == 1, f"mutant anchor not unique: {old!r}"
    return src.replace(old, new)
