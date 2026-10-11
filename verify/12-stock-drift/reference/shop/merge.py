"""Merge two open orders of the same customer into one shipment."""
from .orders import Line


def merge(book, keep_id, other_id):
    """Move all lines of `other_id` into `keep_id`; `other_id` ends up cancelled."""
    keep, other = book.orders[keep_id], book.orders[other_id]
    if keep_id == other_id or keep.customer != other.customer:
        raise ValueError("can only merge two different orders of one customer")
    if keep.status != "open" or other.status != "open":
        raise ValueError("can only merge open orders")
    for line in other.lines:
        try:
            existing = keep.line(line.sku)
        except KeyError:
            keep.lines.append(Line(line.sku, line.qty, line.shipped))
        else:
            existing.qty += line.qty
            existing.shipped += line.shipped
    other.status = "cancelled"  # its reservations now belong to `keep`
