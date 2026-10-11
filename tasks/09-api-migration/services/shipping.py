from legacy_http import BASE_URL, LegacyHTTPError, get_json, post_json


def quote(order_id: int, country: str) -> dict | None:
    return get_json(f"{BASE_URL}/shipping/quote", params={"order": order_id, "country": country}, timeout=15)


def track(tracking_no: str) -> dict | None:
    try:
        return get_json(f"{BASE_URL}/shipping/track/{tracking_no}")
    except LegacyHTTPError as e:
        if e.code == 503:  # carrier API down; the UI shows "unknown"
            return {"status": "unknown"}
        raise


def create_label(order_id: int) -> dict:
    return post_json(f"{BASE_URL}/shipping/labels", {"order": order_id}, timeout=30)
