import json
import logging
import os
import tempfile
import unittest

from app import settings as cfg
from app.client import connect_args
from app.features import all_enabled, enabled
from app.logsetup import level
from app.retry import call_with_retry


class Settings(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "settings.json")

    def tearDown(self):
        self.dir.cleanup()

    def write(self, data):
        with open(self.path, "w") as f:
            json.dump(data, f)

    def test_load_and_defaults(self):
        self.write({"host": "api.example.com", "retries": 2})
        s = cfg.load(self.path)
        self.assertEqual((s.host, s.port, s.max_attempts), ("api.example.com", 8080, 3))

    def test_round_trip(self):
        self.write({"host": "h", "port": 9000, "timeout": 5, "log_level": "debug"})
        cfg.save(cfg.load(self.path), self.path)
        self.assertEqual(cfg.load(self.path).port, 9000)

    def test_bad_port(self):
        self.write({"port": 70000})
        with self.assertRaises(cfg.ConfigError):
            cfg.load(self.path)


class Callers(unittest.TestCase):
    def test_connect_args(self):
        self.assertEqual(connect_args(cfg.Settings(timeout_ms=2500)), {"address": ("localhost", 8080), "timeout": 2.5})

    def test_retry(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise OSError("down")
            return "ok"

        self.assertEqual(call_with_retry(cfg.Settings(max_attempts=3), flaky, sleep=lambda s: None), "ok")

    def test_features_and_logging(self):
        s = cfg.Settings(features=["b", "a"], log_level="WARNING")
        self.assertTrue(enabled(s, "a"))
        self.assertEqual(all_enabled(s), ["a", "b"])
        self.assertEqual(level(s), logging.WARNING)


if __name__ == "__main__":
    unittest.main()
