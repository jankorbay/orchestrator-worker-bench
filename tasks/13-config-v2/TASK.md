# Task 13 — Settings file format v2

`app/settings.py` reads and writes the service's settings file in format v1. We are
moving to format v2, specified in `MIGRATION.md`. Implement it with this compatibility
contract:

1. `load(path)` reads both formats and always returns the v2 `Settings` described in
   `MIGRATION.md`. A file whose `version` is anything other than missing (v1) or `2`
   raises `ConfigError`. Invalid values in either format raise `ConfigError`.
2. `save(settings, path)` validates and always writes format v2, including
   `"version": 2`, with the keys from `extra` at the top level. Loading a file and saving
   it again must not lose any key, in either format.
3. New: `migrate_file(path)` upgrades a settings file in place. For a v1 file it first
   copies the original file byte for byte to `path + ".v1.bak"`, then writes the v2
   version to `path`, and returns `True`. A v2 file is left completely untouched (no
   write, no backup) and it returns `False`. An invalid file raises `ConfigError` and
   nothing is written.
4. `Settings` must no longer have the v1 fields. Update every caller in `app/` to the
   new fields so that the program behaves exactly as before for an equivalent
   configuration: same connect timeout in seconds, same number of attempts and the same
   back-off delays, same feature flags, same log level.
5. Keep the code compatible with Python 3.10.

`test_app.py` holds the current tests. Update them to the new format and add tests for
the contract above.

Run tests with: `python3 -m unittest -q` (from this directory).
