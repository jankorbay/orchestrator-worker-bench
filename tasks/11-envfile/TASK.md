# Task 11 — A real `.env` parser

`envfile.parse` is a quick hack: it strips quotes and nothing else. Teams now rely on
quoting, escapes and variable references, so rewrite `parse(text, environ=None)` to follow
the format below **exactly**. Keep `parse`, `load` and `ParseError` (with its `.line`
attribute) as they are. `environ` is a dict of outside variables; `None` means
`os.environ`.

## Format

**Lines.** The text is split into physical lines on `\n`; a `\r` at the end of a line is
dropped. Line numbers are 1-based physical line numbers. Lines that are empty or only
whitespace, and lines whose first non-whitespace character is `#`, are skipped.

**Assignments.** Every other line is: optional whitespace, optionally the word `export`
followed by one or more spaces or tabs, a KEY, optional whitespace, `=`, optional
whitespace, then a VALUE. KEY must match `[A-Za-z_][A-Za-z0-9_]*` (so `export=1` assigns
the key `export`). Any line that does not have this shape raises `ParseError`. If a key is
assigned more than once, the last assignment wins.

**Values.** The first character of the value picks its form:

- `'` — **single-quoted**: everything up to the next `'`, taken literally. No escapes, no
  variable references.
- `"` — **double-quoted**: everything up to the next `"` that is not escaped. Escapes:
  `\n` (newline), `\t` (tab), `\"`, `\\`, and `\$` (a literal `$`). A backslash before any
  other character is kept together with that character (`"\d"` is `\d`). Variable
  references are expanded.
- anything else — **unquoted**: the rest of the physical line. A `#` at the start of the
  value or directly after a space or tab starts a comment and ends the value (`KEY=a#b`
  gives `a#b`; `KEY=a #b` and `KEY=#b` give `a` and the empty string).
  Trailing whitespace is then removed. Quote characters inside are literal. Variable
  references are expanded. An empty value (`KEY=`) is the empty string.

Quoted values may span several physical lines; the newlines are part of the value. After
the closing quote, only whitespace and an optional `#` comment may follow on that line;
anything else raises `ParseError` with the number of the line holding the closing quote.
A quote that is never closed raises `ParseError` with the number of the line where the
value started. Errors on later lines always report their physical line number.

**Variable references** (in unquoted and double-quoted values):

- `$NAME` — NAME is the longest run of characters matching `[A-Za-z_][A-Za-z0-9_]*`.
- `${NAME}`.
- `${NAME:-default}` — `default` if NAME is unset or empty, else NAME's value. `default`
  is literal text up to the first `}` (no nested references, no escapes).
- A `$` not followed by a letter, `_` or `{` is a literal `$`.
- `${` with no `}` after it in the value, or with an invalid NAME inside, raises
  `ParseError` with the number of the line where the value started.

A name is looked up first among the keys assigned on **earlier** lines of the same text
(their current value at that point, even if empty), then in `environ`. If it is in
neither, it expands to the empty string.

`test_envfile.py` holds the current tests; add tests for the new behaviour.

Run tests with: `python3 -m unittest -q` (from this directory).
