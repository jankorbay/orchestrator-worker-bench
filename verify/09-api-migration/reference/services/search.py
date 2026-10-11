from api import get_json


def search_products(query: str, limit: int = 20) -> list[dict]:
    return get_json("/search", params={"q": query, "limit": limit})["results"]


def suggest(prefix: str) -> list[str]:
    # The suggest service answers 404 when it has nothing for the prefix.
    return get_json("/search/suggest", params={"prefix": prefix}, timeout=1) or []
