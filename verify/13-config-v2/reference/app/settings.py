"""Application settings, stored as a JSON file (format v2, reads v1). See MIGRATION.md."""
import json
import shutil
from dataclasses import dataclass, field
from typing import Optional

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
V1_KEYS = {"host", "port", "timeout", "retries", "log_level", "features"}
V2_KEYS = {"version", "server", "timeout_ms", "retry", "log_level", "features"}


class ConfigError(ValueError):
    pass


@dataclass
class Settings:
    host: str = "localhost"
    port: int = 8080
    timeout_ms: Optional[int] = 10000  # None means no timeout
    max_attempts: int = 1              # total attempts, including the first
    log_level: str = "INFO"
    features: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)  # unknown top-level keys, kept as they are


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def validate(s):
    if not isinstance(s.host, str):
        raise ConfigError(f"bad host {s.host!r}")
    if not _is_int(s.port) or not 1 <= s.port <= 65535:
        raise ConfigError(f"bad port {s.port!r}")
    if s.timeout_ms is not None and (not _is_int(s.timeout_ms) or s.timeout_ms <= 0):
        raise ConfigError("timeout_ms must be null or a positive int")
    if not _is_int(s.max_attempts) or s.max_attempts < 1:
        raise ConfigError("max_attempts must be >= 1")
    if s.log_level not in LOG_LEVELS:
        raise ConfigError(f"bad log level {s.log_level!r}")
    if not isinstance(s.features, list) or not all(isinstance(f, str) for f in s.features):
        raise ConfigError("features must be a list of strings")


def _from_v1(data):
    timeout, retries = data.get("timeout", 10), data.get("retries", 0)
    level, features = data.get("log_level", "info"), data.get("features", "")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout < 0:
        raise ConfigError("timeout must be >= 0")
    if not _is_int(retries) or retries < 0:
        raise ConfigError("retries must be >= 0")
    if not isinstance(level, str) or not isinstance(features, str):
        raise ConfigError("bad log_level or features")
    return Settings(host=data.get("host", "localhost"), port=data.get("port", 8080),
                    timeout_ms=round(timeout * 1000) or None, max_attempts=retries + 1,
                    log_level=level.upper(), features=[f.strip() for f in features.split(",") if f.strip()],
                    extra={k: v for k, v in data.items() if k not in V1_KEYS})


def _from_v2(data):
    server, retry = data.get("server", {}), data.get("retry", {})
    level = data.get("log_level", "INFO")
    if not isinstance(server, dict) or not isinstance(retry, dict) or not isinstance(level, str):
        raise ConfigError("bad server, retry or log_level")
    return Settings(host=server.get("host", "localhost"), port=server.get("port", 8080),
                    timeout_ms=data.get("timeout_ms", 10000), max_attempts=retry.get("max_attempts", 1),
                    log_level=level.upper(), features=data.get("features", []),
                    extra={k: v for k, v in data.items() if k not in V2_KEYS})


def _parse(data):
    if not isinstance(data, dict):
        raise ConfigError("settings must be a JSON object")
    if "version" not in data:
        s = _from_v1(data)
    elif data["version"] == 2 and not isinstance(data["version"], bool):
        s = _from_v2(data)
    else:
        raise ConfigError(f"unknown settings version {data['version']!r}")
    validate(s)
    return s


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load(path):
    return _parse(_read(path))


def _to_v2(s):
    validate(s)
    return {**s.extra, "version": 2, "server": {"host": s.host, "port": s.port}, "timeout_ms": s.timeout_ms,
            "retry": {"max_attempts": s.max_attempts}, "log_level": s.log_level, "features": list(s.features)}


def save(s, path):
    data = _to_v2(s)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def migrate_file(path):
    """Upgrade a v1 settings file to v2 in place, keeping a backup. Returns True if it changed."""
    data = _read(path)
    s = _parse(data)
    if "version" in data:
        return False
    shutil.copyfile(path, path + ".v1.bak")
    save(s, path)
    return True
