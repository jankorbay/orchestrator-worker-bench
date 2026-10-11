import unittest

import api
from httpclient import Response
from services import orders, users


class FakeClient:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []

    def get(self, path, params=None, timeout=None):
        self.calls.append(("GET", path, params, timeout))
        return self.responses.pop(0)

    def post(self, path, json=None, timeout=None):
        self.calls.append(("POST", path, json, timeout))
        return self.responses.pop(0)


class UserTests(unittest.TestCase):
    def test_get_user(self):
        api.set_client(fake := FakeClient(Response(200, {"id": 1, "name": "Ada"})))
        self.assertEqual(users.get_user(1)["name"], "Ada")
        self.assertEqual(fake.calls, [("GET", "/users/1", None, 10)])

    def test_create_user_conflict(self):
        api.set_client(FakeClient(Response(409)))
        self.assertIsNone(users.create_user("Ada", "ada@example.com"))


class OrderTests(unittest.TestCase):
    def test_pagination(self):
        api.set_client(FakeClient(Response(200, {"items": [1, 2], "has_more": True}),
                                  Response(200, {"items": [3], "has_more": False})))
        self.assertEqual(orders.all_orders(7), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
