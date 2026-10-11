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
