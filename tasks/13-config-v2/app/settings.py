"""Application settings, stored as a JSON file (format v1)."""
import json
from dataclasses import asdict, dataclass, fields

LOG_LEVELS = ("debug", "info", "warning", "error")


class ConfigError(ValueError):
    pass


@dataclass
class Settings:
    host: str = "localhost"
    port: int = 8080
    timeout: float = 10    # seconds; 0 means no timeout
    retries: int = 0       # extra attempts after the first one fails
    log_level: str = "info"
    features: str = ""     # comma-separated feature flags


def validate(s):
    if not isinstance(s.port, int) or not 1 <= s.port <= 65535:
        raise ConfigError(f"bad port {s.port!r}")
    if s.timeout < 0:
        raise ConfigError("timeout must be >= 0")
    if s.retries < 0:
        raise ConfigError("retries must be >= 0")
    if s.log_level.lower() not in LOG_LEVELS:
        raise ConfigError(f"bad log level {s.log_level!r}")


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    known = {f.name for f in fields(Settings)}
    s = Settings(**{k: v for k, v in data.items() if k in known})
    validate(s)
    return s


def save(s, path):
    validate(s)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(s), f, indent=2)
