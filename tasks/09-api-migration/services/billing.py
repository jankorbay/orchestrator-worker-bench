from legacy_http import BASE_URL, LegacyHTTPError, get_json, post_json


def get_invoice(invoice_id: str) -> dict | None:
    return get_json(f"{BASE_URL}/invoices/{invoice_id}")


def invoices_for(user_id: int) -> list[dict]:
    return get_json(f"{BASE_URL}/invoices", params={"user_id": user_id})["items"]


def pay(invoice_id: str, amount_cents: int) -> dict:
    try:
        return post_json(f"{BASE_URL}/invoices/{invoice_id}/pay", {"amount_cents": amount_cents}, timeout=20)
    except LegacyHTTPError as e:
        if e.code == 402:
            return {"paid": False, "reason": "declined"}
        raise
