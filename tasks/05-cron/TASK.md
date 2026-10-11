# Task 05 — Next run time for a cron expression

Implement `next_run(expr, after)` in `cron.py` (stdlib only). It returns the earliest
`datetime` **strictly after** `after` (naive datetimes, seconds and microseconds = 0)
that matches the 5-field cron expression `expr`.

Fields, separated by whitespace, in order:

| field        | allowed |
|--------------|---------|
| minute       | 0-59    |
| hour         | 0-23    |
| day of month | 1-31    |
| month        | 1-12    |
| day of week  | 0-7, where 0 and 7 both mean Sunday, 1 = Monday |

Each field is a comma-separated list of items. An item is one of:
- `*` — every value in the field's range
- `N` — a single value
- `N-M` — inclusive range, requires N <= M
- any of the above followed by `/S` (S >= 1): every S-th value of that range, starting at
  its first value. `N/S` means `N-<field max>/S`.

Day matching: if both day-of-month and day-of-week are restricted (their text does not
start with `*`), a day matches when **either** matches. Otherwise a day must match
**both**.

Raise `ValueError` for anything malformed: wrong number of fields, empty items,
non-numeric values, values out of range, a reversed range, or a step of 0. Also raise
`ValueError` if no matching time exists within 10 years after `after`.

Every call must return quickly (well under 0.1 s), including for expressions that never
match. A minute-by-minute scan over 10 years is too slow.

`test_cron.py` has a couple of starter tests.

Run with: `python3 -m unittest -q` (from this directory).
