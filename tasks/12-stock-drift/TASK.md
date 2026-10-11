# Task 12 — Stock drifts away from reality

`shop/` keeps warehouse stock and customer orders. Open orders reserve stock; the web shop
shows `on_hand - reserved` as available. Operations reported three problems this month:

1. After the nightly import, which rejected a few orders for lack of stock, the shop
   showed several items as sold out although the warehouse had them and no open order
   was holding them.
2. We oversold the blue mug (`MUG-BL`): the shop accepted more mugs than we had. The
   customers involved had merged orders or changed quantities shortly before.
3. A manual stock audit found `reserved` numbers that match no combination of open
   orders, mostly for items where part of an order had already shipped.

Find every code path that breaks the rules below and fix it at the cause. The rules are
the contract; the reports are only the symptoms people happened to notice.

## Rules

1. For every SKU, `stock.reserved[sku]` equals the sum of `qty - shipped` over the lines
   of all **open** orders with that SKU (a missing key counts as 0). Shipped and
   cancelled orders hold nothing.
2. `0 <= reserved[sku] <= on_hand[sku]` for every SKU, at all times. Nothing can be
   reserved, ordered or changed beyond what is on hand; that raises `OutOfStock`.
3. Every public operation (`OrderBook.place`, `cancel`, `change_qty`, `fulfilment.ship`,
   `merge.merge`, `importer.import_orders`) either fully succeeds or raises and leaves
   stock and every order exactly as they were. An order may list the same SKU more
   than once.
4. Only **open** orders can be cancelled, changed, shipped from or merged; anything else
   raises `ValueError`.
5. After `merge(book, keep_id, other_id)`, `keep_id` holds all the lines and is still
   open, and `other_id` is cancelled.

Keep the public API (names, arguments, return values). `test_shop.py` holds the current
tests; add tests that would have caught these problems.

Run tests with: `python3 -m unittest -q` (from this directory).
