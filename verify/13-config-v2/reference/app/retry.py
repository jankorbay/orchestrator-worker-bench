"""Retrying calls to the upstream service."""
import time


def call_with_retry(settings, fn, sleep=time.sleep):
    """Call fn(); on OSError try again, up to the configured number of attempts."""
    for attempt in range(settings.max_attempts):
        try:
            return fn()
        except OSError:
            if attempt == settings.max_attempts - 1:
                raise
            sleep(0.1 * 2 ** attempt)
