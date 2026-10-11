# Task 06 — Security review of `app.py`

Review `app.py` for security vulnerabilities. Do not modify `app.py`. Assume every
function argument comes straight from an untrusted HTTP request, and the database,
file system and `/opt/reports/bin/*` binaries are trusted.

Write your findings to `findings.json` in this directory:

```json
[
  {"line": 42, "title": "short name of the vulnerability", "fix": "one-sentence fix"}
]
```

- One entry per distinct vulnerability. `line` is the line number of the vulnerable statement.
- Scoring: each real vulnerability found earns points; each reported "vulnerability"
  that is not real costs points. Only report what you would block a merge for.
