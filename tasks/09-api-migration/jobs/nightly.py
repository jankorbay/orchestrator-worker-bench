"""Nightly maintenance jobs (run by cron)."""
from legacy_http import BASE_URL, get_json
from services.notifications import send_email


def stale_carts(days: int = 7) -> list[dict]:
    # Slow endpoint: it scans every open cart.
    return get_json(f"{BASE_URL}/carts", params={"stale_days": days}, timeout=60)["items"]


def remind_stale_carts(days: int = 7) -> int:
    carts = stale_carts(days)
    for cart in carts:
        send_email(cart["email"], "cart-reminder", {"cart_id": cart["id"]})
    return len(carts)
