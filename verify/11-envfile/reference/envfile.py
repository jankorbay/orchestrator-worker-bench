"""Load `.env` files into a dict. The format is described in TASK.md."""
import os
import re

KEY = re.compile(r"[ \t]*(?:export[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "$": "\0"}  # \0 marks a literal $
TAIL = re.compile(r"[ \t]*(#.*)?")


class ParseError(ValueError):
    def __init__(self, message, line):
        super().__init__(f"line {line}: {message}")
        self.line = line


def _expand(value, lookup, line):
    out, i = [], 0
    while i < len(value):
        c = value[i]
        if c != "$":
            out.append("$" if c == "\0" else c)
            i += 1
        elif value.startswith("${", i):
            end = value.find("}", i)
            if end < 0:
                raise ParseError("unterminated ${", line)
            name, sep, default = value[i + 2:end].partition(":-")
            if not NAME.fullmatch(name):
                raise ParseError(f"invalid variable name {name!r}", line)
            v = lookup(name)
            out.append(default if sep and not v else v)
            i = end + 1
        elif m := NAME.match(value, i + 1):
            out.append(lookup(m.group()))
            i = m.end()
        else:
            out.append("$")
            i += 1
    return "".join(out)


def parse(text, environ=None):
    """Parse the text of a .env file and return {key: value}."""
    environ = os.environ if environ is None else environ
    result = {}

    def lookup(name):
        return result[name] if name in result else environ.get(name, "")

    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in text.split("\n")]
    n = 0
    while n < len(lines):
        start, line = n + 1, lines[n]
        n += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = KEY.match(line)
        if not m:
            raise ParseError("expected KEY=value", start)
        key, rest = m.group(1), line[m.end():]
        if rest[:1] in ("'", '"'):
            quote, buf, i, text_ = rest[0], [], 1, rest
            while True:
                if i >= len(text_):
                    if n >= len(lines):
                        raise ParseError("unterminated quote", start)
                    buf.append("\n")
                    text_, i = lines[n], 0
                    n += 1
                    continue
                c = text_[i]
                if c == quote:
                    break
                if quote == '"' and c == "\\" and i + 1 < len(text_):
                    nxt = text_[i + 1]
                    buf.append(ESCAPES.get(nxt, "\\" + nxt))
                    i += 2
                    continue
                buf.append(c)
                i += 1
            if not TAIL.fullmatch(text_[i + 1:]):
                raise ParseError("unexpected text after closing quote", n)
            value = "".join(buf)
            result[key] = value if quote == "'" else _expand(value, lookup, start)
        else:
            value = re.split(r"(?:^|[ \t])#", rest, maxsplit=1)[0].rstrip()
            result[key] = _expand(value, lookup, start)
    return result


def load(path, environ=None):
    """Parse the .env file at `path`."""
    with open(path, encoding="utf-8") as f:
        return parse(f.read(), os.environ if environ is None else environ)
