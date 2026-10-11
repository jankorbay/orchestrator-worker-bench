# Task 03 — Rename and annotate the `shop` package

Clean-up of the `shop/` package. Behaviour must not change.

1. Rename `fmt_money` to `format_money` everywhere. The old name must not appear
   anywhere in `shop/` afterwards (no alias, no import `as fmt_money`, no comment).
2. Add full type hints (every parameter and the return type) to every public function and
   method in `shop/`. Public = name does not start with `_`, plus `__init__`.
3. Give every public function and method (same definition) a one-line docstring.

`test_shop.py` checks the current behaviour; keep it passing (update it for the rename).

Run with: `python3 -m unittest -q` (from this directory).
