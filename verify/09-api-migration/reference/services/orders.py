from api import get_json, post_json
from httpclient import HTTPError


def get_order(order_id: int) -> dict | None:
    return get_json(f"/orders/{order_id}")


def list_orders(user_id: int, status: str | None = None) -> list[dict]:
    params = {"user_id": user_id}
    if status:
        params["status"] = status
    return get_json(f"/orders", params=params)["items"]


def all_orders(user_id: int) -> list[dict]:
    """Every order of a user, following pagination."""
    page, out = 1, []
    while True:
        data = get_json(f"/orders", params={"user_id": user_id, "page": page})
        out += data["items"]
        if not data["has_more"]:
            return out
        page += 1


def order_total(order_id: int) -> int:
    return get_json(f"/orders/{order_id}/total", timeout=2)["total_cents"]


def cancel_order(order_id: int) -> bool:
    """True if cancelled; False if the order doesn't exist or can't be cancelled any more."""
    try:
        post_json(f"/orders/{order_id}/cancel", {}, timeout=5)
        return True
    except HTTPError as e:
        if e.status in (404, 409):
            return False
        raise
