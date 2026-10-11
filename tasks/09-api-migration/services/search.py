import urllib.parse

from legacy_http import BASE_URL, get_json


def search_products(query: str, limit: int = 20) -> list[dict]:
    q = urllib.parse.quote(query)
    return get_json(f"{BASE_URL}/search?q={q}&limit={limit}")["results"]


def suggest(prefix: str) -> list[str]:
    # The suggest service answers 404 when it has nothing for the prefix.
    return get_json(f"{BASE_URL}/search/suggest?prefix={urllib.parse.quote(prefix)}", timeout=1) or []
