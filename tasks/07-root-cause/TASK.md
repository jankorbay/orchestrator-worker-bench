# Task 07 — Billing complaints

Two customer complaints came in this week. Find the root causes in `billing/` and fix
them. `BILLING_RULES.md` is the source of truth for how billing must work. Fix causes, not
symptoms: other customers are affected by the same bugs in ways nobody reported yet.

## Complaint 1 — Brightside Ltd (UK, billed in GBP)

> We used the WELCOME20 code (€20 off) on invoice 2026-0412 but we were charged £55.88.
> That's more than €20 off, isn't it?

Order: 1 × Mechanical keyboard (KB-01, €28.21), 3 × Wireless mouse (MS-02, €11.19 each),
1 × USB headset (HS-03, €26.97). Finance recalculated it by hand:

| Line  | Discount | Net    |
|-------|----------|--------|
| KB-01 | £5.44    | £18.68 |
| MS-02 | £6.46    | £22.24 |
| HS-03 | £5.20    | £17.86 |
| Total |          | £58.78 |

## Complaint 2 — Müller Technik GmbH (Austria, billed in EUR)

> We are a VAT-registered business (VAT ID `atu-1234.5678`) and should be invoiced under
> reverse charge, but invoice 2026-0419 charged us 20% Austrian VAT (€87.60).

Order: 2 × 27" monitor (MON-27, €219.00 each). The expected total is €438.00 with no VAT
and the reverse-charge note.

Keep the existing public functions and their signatures. `test_billing.py` holds the
current tests; add regression tests for what you fix.

Run tests with: `python3 -m unittest -q` (from this directory).
