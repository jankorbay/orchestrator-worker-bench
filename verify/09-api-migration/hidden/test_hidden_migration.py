"""Behaviour of every migrated caller, checked through a fake client.

Each case: (name, call, responses, expected requests, expected result or exception).
A request is (method, path, params-or-json, effective timeout).
"""
import pathlib
import unittest
import urllib.request


def _no_network(*args, **kwargs):
    raise OSError("network disabled in tests: a caller still bypasses api.get_client()")


urllib.request.urlopen = _no_network

import api
from httpclient import HTTPError, Response
from jobs import nightly
from services import billing, inventory, notifications, orders, search, shipping, users

NEW_DEFAULT_TIMEOUT = 30


def norm(value):
    """Compare params as the URL would carry them (strings); treat {} and None alike."""
    if not value:
        return None
    if isinstance(value, dict):
        return {k: v if isinstance(v, (dict, list)) else str(v) for k, v in value.items()}
    return value


class FakeClient:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def get(self, path, params=None, timeout=None):
        self.calls.append(("GET", path, norm(params), NEW_DEFAULT_TIMEOUT if timeout is None else timeout))
        return self.responses.pop(0)

    def post(self, path, json=None, timeout=None):
        self.calls.append(("POST", path, json, NEW_DEFAULT_TIMEOUT if timeout is None else timeout))
        return self.responses.pop(0)


R = Response
ITEMS = {"items": [{"id": 1}]}

CASES = [
    # users
    ("get_user", lambda: users.get_user(1), [R(200, {"id": 1})], [("GET", "/users/1", None, 10)], {"id": 1}),
    ("get_user_404", lambda: users.get_user(1), [R(404)], [("GET", "/users/1", None, 10)], None),
    ("get_user_500", lambda: users.get_user(1), [R(500)], [("GET", "/users/1", None, 10)], HTTPError),
    ("find_user_by_email", lambda: users.find_user_by_email("a@x.io"), [R(200, {"id": 2})],
     [("GET", "/users", {"email": "a@x.io"}, 10)], {"id": 2}),
    ("user_exists_404", lambda: users.user_exists(4), [R(404)], [("GET", "/users/4", None, 3)], False),
    ("user_exists_200", lambda: users.user_exists(4), [R(200, {"id": 4})], [("GET", "/users/4", None, 3)], True),
    ("create_user", lambda: users.create_user("Ada", "a@x.io"), [R(201, {"id": 5})],
     [("POST", "/users", {"name": "Ada", "email": "a@x.io"}, 10)], {"id": 5}),
    ("create_user_409", lambda: users.create_user("Ada", "a@x.io"), [R(409)],
     [("POST", "/users", {"name": "Ada", "email": "a@x.io"}, 10)], None),
    ("create_user_500", lambda: users.create_user("Ada", "a@x.io"), [R(500)],
     [("POST", "/users", {"name": "Ada", "email": "a@x.io"}, 10)], HTTPError),
    ("update_email", lambda: users.update_email(1, "b@x.io"), [R(204)],
     [("POST", "/users/1/email", {"email": "b@x.io"}, 5)], None),
    ("update_email_404_raises", lambda: users.update_email(1, "b@x.io"), [R(404)],
     [("POST", "/users/1/email", {"email": "b@x.io"}, 5)], HTTPError),
    # orders
    ("get_order_404", lambda: orders.get_order(3), [R(404)], [("GET", "/orders/3", None, 10)], None),
    ("list_orders", lambda: orders.list_orders(7), [R(200, ITEMS)],
     [("GET", "/orders", {"user_id": "7"}, 10)], ITEMS["items"]),
    ("list_orders_status", lambda: orders.list_orders(7, "open"), [R(200, ITEMS)],
     [("GET", "/orders", {"user_id": "7", "status": "open"}, 10)], ITEMS["items"]),
    ("all_orders_pages", lambda: orders.all_orders(7),
     [R(200, {"items": [1, 2], "has_more": True}), R(200, {"items": [3], "has_more": False})],
     [("GET", "/orders", {"user_id": "7", "page": "1"}, 10), ("GET", "/orders", {"user_id": "7", "page": "2"}, 10)],
     [1, 2, 3]),
    ("order_total", lambda: orders.order_total(3), [R(200, {"total_cents": 990})],
     [("GET", "/orders/3/total", None, 2)], 990),
    ("cancel_order", lambda: orders.cancel_order(3), [R(200, {"ok": True})],
     [("POST", "/orders/3/cancel", {}, 5)], True),
    ("cancel_order_404", lambda: orders.cancel_order(3), [R(404)], [("POST", "/orders/3/cancel", {}, 5)], False),
    ("cancel_order_409", lambda: orders.cancel_order(3), [R(409)], [("POST", "/orders/3/cancel", {}, 5)], False),
    ("cancel_order_500", lambda: orders.cancel_order(3), [R(500)], [("POST", "/orders/3/cancel", {}, 5)], HTTPError),
    # inventory
    ("stock_level", lambda: inventory.stock_level("A1"), [R(200, {"available": 4})],
     [("GET", "/stock/A1", None, 10)], 4),
    ("stock_level_404", lambda: inventory.stock_level("A1"), [R(404)], [("GET", "/stock/A1", None, 10)], 0),
    ("reserved", lambda: inventory.reserved("A1"), [R(200, {"count": 2})], [("GET", "/stock/A1/reserved", None, 2)], 2),
    ("warehouses", lambda: inventory.warehouses(), [R(200, ITEMS)], [("GET", "/warehouses", None, 10)], ITEMS["items"]),
    ("low_stock", lambda: inventory.low_stock(3), [R(200, ITEMS)],
     [("GET", "/stock", {"below": "3"}, 10)], ITEMS["items"]),
    # search
    ("search_products", lambda: search.search_products("red shoes & socks", 5), [R(200, {"results": [1]})],
     [("GET", "/search", {"q": "red shoes & socks", "limit": "5"}, 10)], [1]),
    ("suggest_404", lambda: search.suggest("ab"), [R(404)], [("GET", "/search/suggest", {"prefix": "ab"}, 1)], []),
    # shipping
    ("quote", lambda: shipping.quote(1, "DE"), [R(200, {"cents": 499})],
     [("GET", "/shipping/quote", {"order": "1", "country": "DE"}, 15)], {"cents": 499}),
    ("track_503", lambda: shipping.track("T9"), [R(503)], [("GET", "/shipping/track/T9", None, 10)],
     {"status": "unknown"}),
    ("track_404", lambda: shipping.track("T9"), [R(404)], [("GET", "/shipping/track/T9", None, 10)], None),
    ("track_500", lambda: shipping.track("T9"), [R(500)], [("GET", "/shipping/track/T9", None, 10)], HTTPError),
    ("create_label", lambda: shipping.create_label(1), [R(201, {"label": "L1"})],
     [("POST", "/shipping/labels", {"order": 1}, 30)], {"label": "L1"}),
    # notifications
    ("send_email", lambda: notifications.send_email("a@x.io", "welcome", {"n": 1}), [R(202)],
     [("POST", "/notify/email", {"to": "a@x.io", "template": "welcome", "data": {"n": 1}}, 10)], None),
    ("preferences_404", lambda: notifications.preferences(1), [R(404)],
     [("GET", "/users/1/notification-prefs", None, 10)], {"email": True, "sms": False}),
    # billing
    ("get_invoice", lambda: billing.get_invoice("I1"), [R(200, {"id": "I1"})],
     [("GET", "/invoices/I1", None, 10)], {"id": "I1"}),
    ("invoices_for", lambda: billing.invoices_for(7), [R(200, ITEMS)],
     [("GET", "/invoices", {"user_id": "7"}, 10)], ITEMS["items"]),
    ("pay", lambda: billing.pay("I1", 990), [R(200, {"paid": True})],
     [("POST", "/invoices/I1/pay", {"amount_cents": 990}, 20)], {"paid": True}),
    ("pay_402", lambda: billing.pay("I1", 990), [R(402)],
     [("POST", "/invoices/I1/pay", {"amount_cents": 990}, 20)], {"paid": False, "reason": "declined"}),
    # jobs outside services/
    ("stale_carts", lambda: nightly.stale_carts(3), [R(200, ITEMS)],
     [("GET", "/carts", {"stale_days": "3"}, 60)], ITEMS["items"]),
    ("remind_stale_carts", lambda: nightly.remind_stale_carts(3),
     [R(200, {"items": [{"id": 8, "email": "c@x.io"}]}), R(202)],
     [("GET", "/carts", {"stale_days": "3"}, 60),
      ("POST", "/notify/email", {"to": "c@x.io", "template": "cart-reminder", "data": {"cart_id": 8}}, 10)], 1),
]


class Migration(unittest.TestCase):
    pass


def make_test(call, responses, expected_calls, expected):
    def test(self):
        fake = FakeClient(responses)
        api.set_client(fake)
        if expected is HTTPError:
            with self.assertRaises(HTTPError):
                call()
        else:
            self.assertEqual(call(), expected)
        self.assertEqual(fake.calls, expected_calls)
    return test


for name, *case in CASES:
    setattr(Migration, f"test_{name}", make_test(*case))


class LegacyRemoved(unittest.TestCase):
    def test_no_references_left(self):
        root = pathlib.Path(__file__).resolve().parent
        self.assertFalse((root / "legacy_http.py").exists(), "legacy_http.py still exists")
        offenders = [str(p.relative_to(root)) for p in root.rglob("*.py")
                     if p.name != pathlib.Path(__file__).name and "legacy_http" in p.read_text()]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
