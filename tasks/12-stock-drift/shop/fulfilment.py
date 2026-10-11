"""Shipping goods for open orders."""


def ship(book, order_id, sku, qty):
    """Ship `qty` units of one order line."""
    order = book.orders[order_id]
    line = order.line(sku)
    if qty <= 0 or qty > line.open_qty:
        raise ValueError("bad shipment quantity")
    book.stock.take(sku, qty)
    line.shipped += qty
    if all(line.open_qty == 0 for line in order.lines):
        order.status = "shipped"
