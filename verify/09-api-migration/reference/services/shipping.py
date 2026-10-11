from api import get_json, post_json
from httpclient import HTTPError


def quote(order_id: int, country: str) -> dict | None:
    return get_json(f"/shipping/quote", params={"order": order_id, "country": country}, timeout=15)


def track(tracking_no: str) -> dict | None:
    try:
        return get_json(f"/shipping/track/{tracking_no}")
    except HTTPError as e:
        if e.status == 503:  # carrier API down; the UI shows "unknown"
            return {"status": "unknown"}
        raise


def create_label(order_id: int) -> dict:
    return post_json(f"/shipping/labels", {"order": order_id}, timeout=30)
