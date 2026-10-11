from shop.money import format_money as _fmt


def _bucket(cents):
    return "large" if cents >= 10_000 else "small"


def daily_report(orders: list[int], currency: str = "USD") -> dict:
    """Summarise a day's order totals (in cents)."""
    total = sum(orders)
    by_size = {}
    for cents in orders:
        by_size[_bucket(cents)] = by_size.get(_bucket(cents), 0) + 1
    return {
        "count": len(orders),
        "total": _fmt(total, currency),
        "average": _fmt(total // len(orders), currency) if orders else _fmt(0, currency),
        "by_size": by_size,
    }
