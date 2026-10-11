from api import get_json, post_json

DEFAULT_PREFS = {"email": True, "sms": False}


def send_email(to: str, template: str, data: dict) -> None:
    post_json(f"/notify/email", {"to": to, "template": template, "data": data})


def preferences(user_id: int) -> dict:
    return get_json(f"/users/{user_id}/notification-prefs") or dict(DEFAULT_PREFS)
