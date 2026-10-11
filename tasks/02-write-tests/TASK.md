# Task 02 — Write tests for the pricing module

`pricing.py` has no tests. Write `test_pricing.py` (stdlib `unittest`, in this
directory) that checks every rule in the module docstring.

How it is scored:
- All your tests must pass against the current `pricing.py`. If any fails, the score is 0.
- Your tests are then run against several hidden copies of `pricing.py`, each with one
  subtle bug. The score is the share of those buggy copies your tests catch.

Do not modify `pricing.py`.

Run with: `python3 -m unittest -q` (from this directory).
