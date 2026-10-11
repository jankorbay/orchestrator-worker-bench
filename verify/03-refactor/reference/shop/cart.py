from shop.money import format_money


class Cart:
    def __init__(self, currency: str = "USD") -> None:
        """Create an empty cart priced in `currency`."""
        self.currency = currency
        self.lines: list[tuple[str, int, int]] = []

    def add(self, name: str, cents: int, qty: int = 1) -> None:
        """Add `qty` units of an item priced at `cents` each."""
        if qty < 1:
            raise ValueError("qty must be >= 1")
        self.lines.append((name, cents, qty))

    def total(self) -> int:
        """Total of all lines in cents."""
        return sum(cents * qty for _, cents, qty in self.lines)

    def summary(self) -> str:
        """One-line human summary of the cart."""
        return f"{len(self.lines)} item(s), total {format_money(self.total(), self.currency)}"
