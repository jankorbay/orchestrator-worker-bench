# Migrating from `legacy_http` to `httpclient`

`legacy_http` is deprecated. Move every caller to the shared client from `api.get_client()`.

Rules:

1. **Behaviour must not change** for any caller: same return values, same exceptions
   handled the same way, same timeouts.
2. Call `api.get_client()` inside the function that makes the request. Never store the
   client at import time (tests swap it with `api.set_client`).
3. Paths are relative to the base URL: `f"{BASE_URL}/users/{id}"` becomes `f"/users/{id}"`.
   Query parameters go in `params=`, never into the path string.
4. **Timeouts**: `legacy_http` defaulted to 10 s; the new client defaults to 30 s. Keep
   each call's effective timeout (pass `timeout=10` where a call relied on the old default).
5. **Errors**: the new client does not raise by itself. `get_json` returned `None` on 404
   and raised `LegacyHTTPError` (status in `.code`) on other errors; `post_json` raised on
   every error status. Use `resp.raise_for_status()` (raises `httpclient.HTTPError`,
   status in `.status`) and check `resp.status` where needed to keep the old behaviour.
6. `resp.json()` returns the parsed body, or `None` for an empty body (like the legacy helpers).
7. When done, delete `legacy_http.py`. Nothing may reference `legacy_http` any more,
   including comments and tests.
