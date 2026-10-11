"""Access to the shared HTTP client."""
from httpclient import Client

BASE_URL = "https://internal.example.com/api"
_client: Client | None = None


def get_client() -> Client:
    """The process-wide client. Call this when you make a request; don't cache it at import time."""
    global _client
    if _client is None:
        _client = Client(BASE_URL)
    return _client


def set_client(client) -> None:
    """Replace the shared client (tests use this to install a fake)."""
    global _client
    _client = client


def get_json(path: str, params: dict | None = None, timeout: float = 10):
    """GET with the old semantics: None on 404, HTTPError on other error statuses."""
    resp = get_client().get(path, params=params, timeout=timeout)
    if resp.status == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def post_json(path: str, data: dict, timeout: float = 10):
    """POST with the old semantics: HTTPError on every error status."""
    resp = get_client().post(path, json=data, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
