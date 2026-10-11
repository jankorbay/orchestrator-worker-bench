"""Connection parameters for the upstream service."""


def connect_args(settings):
    """Keyword arguments for socket.create_connection."""
    timeout = None if settings.timeout_ms is None else settings.timeout_ms / 1000
    return {"address": (settings.host, settings.port), "timeout": timeout}
