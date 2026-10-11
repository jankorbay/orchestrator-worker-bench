# Task 01 — Fix the inventory bugs

`inventory.py` has bugs. Users reported:

1. "Page 1 of the item list shows what should be page 2."
2. "Low-stock alerts miss some items that should be flagged."
3. "Tags show up on items we never tagged."

Fix the bugs in `inventory.py`. Keep every function name and its parameters
callable the same way (adding a safer default is fine). Don't break the other
functions. `test_inventory.py` has a couple of tests; it is not complete.

Run tests with: `python3 -m unittest -q` (from this directory).
