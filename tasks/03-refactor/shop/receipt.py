from shop import money


def render_line(name, cents, qty, currency="USD"):
    return f"{qty} x {name:<12} {money.fmt_money(cents * qty, currency):>12}"


def render_receipt(cart):
    rows = [render_line(n, c, q, cart.currency) for n, c, q in cart.lines]
    rows.append("-" * 29)
    rows.append(f"{'TOTAL':<16} {money.fmt_money(cart.total(), cart.currency):>12}")
    return "\n".join(rows)
