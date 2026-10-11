from api import get_json, post_json
from httpclient import HTTPError


def get_user(user_id: int) -> dict | None:
    return get_json(f"/users/{user_id}")


def find_user_by_email(email: str) -> dict | None:
    return get_json(f"/users", params={"email": email})


def user_exists(user_id: int) -> bool:
    return get_json(f"/users/{user_id}", timeout=3) is not None


def create_user(name: str, email: str) -> dict | None:
    """Create a user. Returns None if the email is already taken."""
    try:
        return post_json(f"/users", {"name": name, "email": email})
    except HTTPError as e:
        if e.status == 409:
            return None
        raise


def update_email(user_id: int, email: str) -> None:
    post_json(f"/users/{user_id}/email", {"email": email}, timeout=5)
