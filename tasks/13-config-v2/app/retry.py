"""Retrying calls to the upstream service."""
import time


def call_with_retry(settings, fn, sleep=time.sleep):
    """Call fn(); on OSError try again, up to the configured retries."""
    for attempt in range(settings.retries + 1):
        try:
            return fn()
        except OSError:
            if attempt == settings.retries:
                raise
            sleep(0.1 * 2 ** attempt)
