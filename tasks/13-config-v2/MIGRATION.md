# Settings file format v2

## The v2 file

```json
{
  "version": 2,
  "server": {"host": "localhost", "port": 8080},
  "timeout_ms": 10000,
  "retry": {"max_attempts": 1},
  "log_level": "INFO",
  "features": ["thumbnails", "beta-ui"]
}
```

Every key except `version` may be missing, also inside `server` and `retry`; a missing
key takes the default shown above (`features` defaults to `[]`).

| Key | Meaning | Valid values |
|---|---|---|
| `server.host` | upstream host | string |
| `server.port` | upstream port | int, 1–65535 |
| `timeout_ms` | connect timeout in **milliseconds**; `null` means no timeout | `null` or int > 0 |
| `retry.max_attempts` | **total** attempts, including the first one | int >= 1 |
| `log_level` | log level | `DEBUG`, `INFO`, `WARNING`, `ERROR`; any case is accepted on load and stored upper case |
| `features` | enabled feature flags, in file order | list of strings |

## The `Settings` object

```python
@dataclass
class Settings:
    host: str = "localhost"
    port: int = 8080
    timeout_ms: int | None = 10000
    max_attempts: int = 1
    log_level: str = "INFO"
    features: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
```

The v1 fields `timeout` and `retries` are gone. `extra` holds every top-level key of the
file that this table does not know (for example `sentry_dsn`), with its value unchanged.

## Reading v1 files

A file without a `version` key is v1. It is validated by the v1 rules (as today), then
converted:

| v1 key | v2 field |
|---|---|
| `host`, `port` | `host`, `port` |
| `timeout` (seconds, int or float; `0` means no timeout) | `timeout_ms` = seconds × 1000 rounded to an int; `0` becomes `None` |
| `retries` (extra attempts after the first) | `max_attempts` = `retries` + 1 |
| `log_level` (any case) | `log_level` in upper case |
| `features` (comma-separated string) | list of the names, whitespace trimmed, empty names dropped, file order kept |
| any other key | kept in `extra` unchanged |

A missing v1 key takes the v1 default (`timeout` 10, `retries` 0, ...), which gives the
same result as the v2 default.
