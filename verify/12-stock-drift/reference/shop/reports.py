"""What the web shop shows."""


def availability(stock):
    """{sku: units a customer can still order}."""
    return {sku: stock.available(sku) for sku in stock.on_hand}
