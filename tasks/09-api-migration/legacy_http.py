"""DEPRECATED HTTP helpers. Use `httpclient` via `api.get_client()` instead (see MIGRATION.md)."""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://internal.example.com/api"


class LegacyHTTPError(Exception):
    def __init__(self, code: int, body: str = ""):
        super().__init__(f"HTTP {code}")
        self.code = code
        self.body = body


def _send(req: urllib.request.Request, timeout: float):
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise LegacyHTTPError(e.code, e.read().decode(errors="replace")) from None


def get_json(url: str, params: dict | None = None, timeout: float = 10):
    """GET and parse JSON. Returns None on 404; raises LegacyHTTPError on any other error status."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        return _send(urllib.request.Request(url), timeout)
    except LegacyHTTPError as e:
        if e.code == 404:
            return None
        raise


def post_json(url: str, data: dict, timeout: float = 10):
    """POST a JSON body. Returns the parsed response, or None for an empty body.
    Raises LegacyHTTPError on any error status (including 404)."""
    req = urllib.request.Request(url, data=json.dumps(data).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    return _send(req, timeout)
