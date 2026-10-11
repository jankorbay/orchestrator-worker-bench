import unittest

from authsvc import sessions, tokens
from authsvc.timeutil import from_wire, to_wire


class Tests(unittest.TestCase):
    def test_session_roundtrip(self):
        s = sessions.create_session(7)
        self.assertFalse(sessions.is_expired(s))
        self.assertEqual(to_wire(from_wire(s["expires"])), s["expires"])

    def test_token_roundtrip(self):
        self.assertEqual(tokens.verify(tokens.issue(7, ["read"]))["sub"], 7)

    def test_tampered_token(self):
        token = tokens.issue(7, ["read"])
        self.assertIsNone(tokens.verify(token[:-1] + ("0" if token[-1] != "0" else "1")))


if __name__ == "__main__":
    unittest.main()
