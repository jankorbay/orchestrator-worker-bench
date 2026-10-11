"""Browser sessions, stored as dicts of wire-format strings."""
import secrets
from datetime import datetime, timedelta

from authsvc.timeutil import from_wire, to_wire

SESSION_TTL = timedelta(hours=12)


def create_session(user_id: int) -> dict:
    now = datetime.utcnow()
    return {"id": secrets.token_hex(8), "user_id": user_id,
            "created": to_wire(now), "expires": to_wire(now + SESSION_TTL)}


def is_expired(session: dict, now: datetime | None = None) -> bool:
    now = now or datetime.utcnow()
    return from_wire(session["expires"]) <= now


def refresh(session: dict) -> dict:
    return {**session, "expires": to_wire(datetime.utcnow() + SESSION_TTL)}


def remaining(session: dict) -> timedelta:
    return from_wire(session["expires"]) - datetime.utcnow()
