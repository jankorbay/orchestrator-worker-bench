"""Tiny inventory helpers used by the warehouse dashboard."""


def paginate(items: list, page: int, per_page: int) -> list:
    """Return the items shown on `page` (pages are 1-based)."""
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
    start = (page - 1) * per_page
    return items[start:start + per_page]


def low_stock(items: list[dict], threshold: int) -> list[str]:
    """Names of items whose quantity is at or below `threshold`, in input order."""
    return [it["name"] for it in items if it["qty"] <= threshold]


def add_tag(item: dict, tag: str, tags: list | None = None) -> dict:
    """Return a copy of `item` with `tag` added to its tags (no duplicates).

    The input item must not be modified.
    """
    tags = list(tags or [])
    tags.extend(t for t in item.get("tags", []) if t not in tags)
    if tag not in tags:
        tags.append(tag)
    return {**item, "tags": tags}


def total_value(items: list[dict]) -> float:
    """Sum of qty * price over all items, rounded to 2 decimals."""
    return round(sum(it["qty"] * it["price"] for it in items), 2)


def restock_plan(items: list[dict], target: int) -> dict[str, int]:
    """How many units to order per item so every item reaches `target`."""
    return {it["name"]: target - it["qty"] for it in items if it["qty"] < target}
