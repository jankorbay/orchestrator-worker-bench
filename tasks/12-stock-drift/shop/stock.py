"""Warehouse stock: what is physically on hand and what open orders have reserved."""


class OutOfStock(Exception):
    pass


class Stock:
    def __init__(self, on_hand=None):
        self.on_hand = dict(on_hand or {})
        self.reserved = {}

    def available(self, sku):
        return self.on_hand.get(sku, 0) - self.reserved.get(sku, 0)

    def reserve(self, sku, qty):
        if qty > self.available(sku):
            raise OutOfStock(f"{sku}: wanted {qty}, available {self.available(sku)}")
        self.reserved[sku] = self.reserved.get(sku, 0) + qty

    def release(self, sku, qty):
        # never let a reservation go negative
        self.reserved[sku] = max(0, self.reserved.get(sku, 0) - qty)

    def take(self, sku, qty):
        """Reserved goods leave the warehouse."""
        self.on_hand[sku] -= qty
        self.reserved[sku] -= qty

    def receive(self, sku, qty):
        self.on_hand[sku] = self.on_hand.get(sku, 0) + qty
