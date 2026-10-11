"""Nightly import of orders from the web shop export."""
from .stock import OutOfStock


def import_orders(book, rows):
    """`rows` are dicts with order_id, customer, sku, qty; rows of one order are adjacent.

    Places every order. Returns the ids of orders rejected for lack of stock.
    """
    rejected, batch, placed = [], [], []
    try:
        for row in rows + [None]:
            if batch and (row is None or row["order_id"] != batch[0]["order_id"]):
                items = [(r["sku"], int(r["qty"])) for r in batch]
                try:
                    placed.append(book.place(batch[0]["order_id"], batch[0]["customer"], items).id)
                except OutOfStock:
                    rejected.append(batch[0]["order_id"])
                batch = []
            if row is not None:
                batch.append(row)
    except Exception:  # all or nothing: undo the orders this import placed
        for order_id in placed:
            book.cancel(order_id)
            del book.orders[order_id]
        raise
    return rejected
