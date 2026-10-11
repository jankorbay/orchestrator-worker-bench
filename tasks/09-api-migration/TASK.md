# Task 09 — Migrate off `legacy_http`

We are retiring our old HTTP helper module. Migrate every caller in this project to the
new `httpclient` (through `api.get_client()`), following `MIGRATION.md` exactly, then
delete `legacy_http.py`.

Callers live in `services/` and elsewhere in the project. `test_services.py` holds the
current tests; they mock `legacy_http`, so update them to use a fake client via
`api.set_client` and keep them passing.

Run tests with: `python3 -m unittest -q` (from this directory).
