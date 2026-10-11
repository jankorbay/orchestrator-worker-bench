from shop.money import fmt_money


class Cart:
    def __init__(self, currency="USD"):
        self.currency = currency
        self.lines = []

    def add(self, name, cents, qty=1):
        if qty < 1:
            raise ValueError("qty must be >= 1")
        self.lines.append((name, cents, qty))

    def total(self):
        return sum(cents * qty for _, cents, qty in self.lines)

    def summary(self):
        return f"{len(self.lines)} item(s), total {fmt_money(self.total(), self.currency)}"
