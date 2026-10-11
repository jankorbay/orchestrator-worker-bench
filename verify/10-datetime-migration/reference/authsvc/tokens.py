"""Short-lived signed access tokens (HMAC, JSON payload with unix timestamps)."""
import base64
import datetime as dt
import hashlib
import hmac
import json
import os

from authsvc.timeutil import from_unix, to_unix

SECRET = os.environ.get("AUTHSVC_TOKEN_SECRET", "dev-only-secret").encode()
TOKEN_TTL = dt.timedelta(minutes=15)


def _sign(body: str) -> str:
    return hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()


def _payload(token: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(token.rpartition(".")[0]))


def encode(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).decode()
    return f"{body}.{_sign(body)}"


def issue(user_id: int, scopes: list[str]) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    return encode({"sub": user_id, "scopes": scopes, "iat": to_unix(now), "exp": to_unix(now + TOKEN_TTL)})


def verify(token: str) -> dict | None:
    """The payload if the signature is valid and the token has not expired, else None."""
    body, _, sig = token.rpartition(".")
    if not hmac.compare_digest(sig, _sign(body)):
        return None
    payload = _payload(token)
    if dt.datetime.now(dt.timezone.utc) >= from_unix(payload["exp"]):
        return None
    return payload


def expires_at(token: str) -> dt.datetime:
    """Expiry shown in the account UI."""
    return from_unix(_payload(token)["exp"])
