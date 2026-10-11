from shop import money
from shop.cart import Cart


def render_line(name: str, cents: int, qty: int, currency: str = "USD") -> str:
    """Render one receipt line."""
    return f"{qty} x {name:<12} {money.format_money(cents * qty, currency):>12}"


def render_receipt(cart: Cart) -> str:
    """Render the full receipt for a cart."""
    rows = [render_line(n, c, q, cart.currency) for n, c, q in cart.lines]
    rows.append("-" * 29)
    rows.append(f"{'TOTAL':<16} {money.format_money(cart.total(), cart.currency):>12}")
    return "\n".join(rows)
