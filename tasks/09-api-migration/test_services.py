import unittest
from unittest import mock

from legacy_http import LegacyHTTPError
from services import orders, users


class UserTests(unittest.TestCase):
    @mock.patch("services.users.get_json", return_value={"id": 1, "name": "Ada"})
    def test_get_user(self, get_json):
        self.assertEqual(users.get_user(1)["name"], "Ada")
        get_json.assert_called_once_with("https://internal.example.com/api/users/1")

    @mock.patch("services.users.post_json", side_effect=LegacyHTTPError(409))
    def test_create_user_conflict(self, post_json):
        self.assertIsNone(users.create_user("Ada", "ada@example.com"))


class OrderTests(unittest.TestCase):
    @mock.patch("services.orders.get_json", side_effect=[
        {"items": [1, 2], "has_more": True}, {"items": [3], "has_more": False}])
    def test_pagination(self, get_json):
        self.assertEqual(orders.all_orders(7), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
