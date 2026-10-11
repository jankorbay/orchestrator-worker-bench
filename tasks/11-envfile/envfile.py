"""Load `.env` files into a dict. The format is described in TASK.md."""
import os


class ParseError(ValueError):
    def __init__(self, message, line):
        super().__init__(f"line {line}: {message}")
        self.line = line


def parse(text, environ=None):
    """Parse the text of a .env file and return {key: value}."""
    result = {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            raise ParseError("expected KEY=value", n)
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        result[key] = value
    return result


def load(path, environ=None):
    """Parse the .env file at `path`."""
    with open(path, encoding="utf-8") as f:
        return parse(f.read(), os.environ if environ is None else environ)
