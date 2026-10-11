"""Connection parameters for the upstream service."""


def connect_args(settings):
    """Keyword arguments for socket.create_connection."""
    timeout = None if settings.timeout == 0 else settings.timeout
    return {"address": (settings.host, settings.port), "timeout": timeout}
