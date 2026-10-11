"""The new HTTP client (session-based, one instance per process)."""
import json as jsonlib
import urllib.error
import urllib.parse
import urllib.request


class HTTPError(Exception):
    def __init__(self, status: int, body=None):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.body = body


class Response:
    def __init__(self, status: int, body=None):
        self.status = status
        self._body = body  # parsed JSON, or None for an empty body

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def json(self):
        """The parsed JSON body, or None if the body was empty."""
        return self._body

    def raise_for_status(self) -> None:
        """Raise HTTPError for 4xx and 5xx responses."""
        if self.status >= 400:
            raise HTTPError(self.status, self._body)


class Client:
    """Paths are relative to base_url, e.g. client.get("/users/42").

    Unlike the old helpers, the client never raises on error statuses by itself: check
    `resp.status` or call `resp.raise_for_status()`. The default timeout is 30 seconds.
    """

    def __init__(self, base_url: str, default_timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout

    def get(self, path: str, params: dict | None = None, timeout: float | None = None) -> Response:
        url = self.base_url + path + ("?" + urllib.parse.urlencode(params) if params else "")
        return self._send(urllib.request.Request(url), timeout)

    def post(self, path: str, json=None, timeout: float | None = None) -> Response:
        req = urllib.request.Request(self.base_url + path, data=jsonlib.dumps(json).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        return self._send(req, timeout)

    def _send(self, req, timeout) -> Response:
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.default_timeout) as resp:
                raw = resp.read()
                return Response(resp.status, jsonlib.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw = e.read()
            return Response(e.code, jsonlib.loads(raw) if raw else None)
