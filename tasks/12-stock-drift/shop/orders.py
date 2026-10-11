"""Orders and the order book. Open orders hold reservations in `Stock`."""
from dataclasses import dataclass, field


@dataclass
class Line:
    sku: str
    qty: int
    shipped: int = 0

    @property
    def open_qty(self):
        return self.qty - self.shipped


@dataclass
class Order:
    id: str
    customer: str
    lines: list = field(default_factory=list)
    status: str = "open"  # open | shipped | cancelled

    def line(self, sku):
        for line in self.lines:
            if line.sku == sku:
                return line
        raise KeyError(sku)


class OrderBook:
    def __init__(self, stock):
        self.stock = stock
        self.orders = {}

    def place(self, order_id, customer, items):
        """Place an order for `items`, a list of (sku, qty). Raises OutOfStock."""
        if order_id in self.orders:
            raise ValueError(f"duplicate order {order_id}")
        lines = []
        for sku, qty in items:
            if qty <= 0:
                raise ValueError("quantity must be positive")
            self.stock.reserve(sku, qty)
            lines.append(Line(sku, qty))
        order = Order(order_id, customer, lines)
        self.orders[order_id] = order
        return order

    def cancel(self, order_id):
        order = self.orders[order_id]
        for line in order.lines:
            self.stock.release(line.sku, line.qty)
        order.status = "cancelled"

    def change_qty(self, order_id, sku, new_qty):
        """Change the ordered quantity of one line. Raises OutOfStock."""
        order = self.orders[order_id]
        line = order.line(sku)
        if order.status != "open" or new_qty < max(line.shipped, 1):
            raise ValueError("cannot change this line")
        self.stock.reserve(sku, new_qty)
        line.qty = new_qty

    def open_orders(self):
        return [o for o in self.orders.values() if o.status == "open"]
