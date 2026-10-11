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


class Files(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "settings.json")

    def tearDown(self):
        self.dir.cleanup()

    def write(self, data):
        with open(self.path, "w") as f:
            f.write(data if isinstance(data, str) else json.dumps(data))

    def read(self):
        with open(self.path) as f:
            return json.load(f)

    def load(self, data):
        self.write(data)
        return cfg.load(self.path)

    def fields(self, s):
        return (s.host, s.port, s.timeout_ms, s.max_attempts, s.log_level, s.features, s.extra)


class LoadV1(Files):
    def test_full_conversion(self):
        s = self.load({"host": "h", "port": 9000, "timeout": 2.5, "retries": 2, "log_level": "debug",
                       "features": " thumbs, ,beta-ui,,x "})
        self.assertEqual(self.fields(s), ("h", 9000, 2500, 3, "DEBUG", ["thumbs", "beta-ui", "x"], {}))

    def test_defaults_match_v2_defaults(self):
        self.assertEqual(self.fields(self.load({})), self.fields(cfg.Settings()))
        self.assertEqual(self.fields(cfg.Settings()), ("localhost", 8080, 10000, 1, "INFO", [], {}))

    def test_zero_timeout_means_none(self):
        self.assertIsNone(self.load({"timeout": 0}).timeout_ms)

    def test_fractional_timeout(self):
        self.assertEqual(self.load({"timeout": 0.25}).timeout_ms, 250)

    def test_unknown_keys_kept(self):
        self.assertEqual(self.load({"port": 1, "sentry_dsn": "x", "limits": {"a": [1]}}).extra,
                         {"sentry_dsn": "x", "limits": {"a": [1]}})

    def test_v1_validation(self):
        for bad in ({"port": 0}, {"port": "80"}, {"timeout": -1}, {"retries": -1}, {"log_level": "loud"}):
            with self.subTest(bad=bad), self.assertRaises(cfg.ConfigError):
                self.load(bad)

    def test_v1_fields_are_gone(self):
        s = self.load({"timeout": 3, "retries": 1})
        self.assertFalse(hasattr(s, "timeout") or hasattr(s, "retries"))


class LoadV2(Files):
    def test_full(self):
        s = self.load({"version": 2, "server": {"host": "h", "port": 1}, "timeout_ms": 1500,
                       "retry": {"max_attempts": 4}, "log_level": "warning", "features": ["b", "a"], "x": 1})
        self.assertEqual(self.fields(s), ("h", 1, 1500, 4, "WARNING", ["b", "a"], {"x": 1}))

    def test_missing_keys_get_defaults(self):
        s = self.load({"version": 2, "server": {"port": 9}, "retry": {}})
        self.assertEqual(self.fields(s), ("localhost", 9, 10000, 1, "INFO", [], {}))

    def test_null_timeout_is_no_timeout(self):
        self.assertIsNone(self.load({"version": 2, "timeout_ms": None}).timeout_ms)

    def test_unknown_version(self):
        for v in (1, 3, "2", None):
            with self.subTest(version=v), self.assertRaises(cfg.ConfigError):
                self.load({"version": v})

    def test_v2_validation(self):
        for bad in ({"server": {"port": 70000}}, {"timeout_ms": 0}, {"timeout_ms": -5}, {"retry": {"max_attempts": 0}},
                    {"log_level": "loud"}, {"features": "a,b"}):
            with self.subTest(bad=bad), self.assertRaises(cfg.ConfigError):
                self.load({"version": 2, **bad})


class Save(Files):
    def test_writes_v2(self):
        cfg.save(cfg.Settings(host="h", timeout_ms=None, max_attempts=2, features=["a"]), self.path)
        self.assertEqual(self.read(), {"version": 2, "server": {"host": "h", "port": 8080}, "timeout_ms": None,
                                       "retry": {"max_attempts": 2}, "log_level": "INFO", "features": ["a"]})

    def test_v1_round_trip_keeps_everything(self):
        self.write({"host": "h", "timeout": 0, "retries": 4, "features": "a,b", "sentry_dsn": "d"})
        cfg.save(cfg.load(self.path), self.path)
        self.assertEqual(self.read(), {"version": 2, "server": {"host": "h", "port": 8080}, "timeout_ms": None,
                                       "retry": {"max_attempts": 5}, "log_level": "INFO", "features": ["a", "b"],
                                       "sentry_dsn": "d"})

    def test_v2_round_trip_is_identity(self):
        data = {"version": 2, "server": {"host": "h", "port": 7}, "timeout_ms": 30, "retry": {"max_attempts": 2},
                "log_level": "ERROR", "features": ["z", "a"], "owner": {"team": "core"}}
        self.write(data)
        cfg.save(cfg.load(self.path), self.path)
        self.assertEqual(self.read(), data)

    def test_save_validates(self):
        with self.assertRaises(cfg.ConfigError):
            cfg.save(cfg.Settings(timeout_ms=0), self.path)
        self.assertFalse(os.path.exists(self.path))


class Migrate(Files):
    V1_TEXT = '{"port": 9000,   "timeout": 0, "retries": 1,\n "log_level": "Debug", "team": "core"}\n'

    def test_v1_is_migrated_with_backup(self):
        self.write(self.V1_TEXT)
        self.assertIs(cfg.migrate_file(self.path), True)
        with open(self.path + ".v1.bak") as f:
            self.assertEqual(f.read(), self.V1_TEXT)
        self.assertEqual(self.read(), {"version": 2, "server": {"host": "localhost", "port": 9000}, "timeout_ms": None,
                                       "retry": {"max_attempts": 2}, "log_level": "DEBUG", "features": [],
                                       "team": "core"})

    def test_v2_is_untouched(self):
        text = '{"version": 2,\n   "timeout_ms": 5}'
        self.write(text)
        mtime = os.stat(self.path).st_mtime_ns
        self.assertIs(cfg.migrate_file(self.path), False)
        with open(self.path) as f:
            self.assertEqual(f.read(), text)
        self.assertEqual(os.stat(self.path).st_mtime_ns, mtime)
        self.assertFalse(os.path.exists(self.path + ".v1.bak"))

    def test_second_run_is_noop(self):
        self.write(self.V1_TEXT)
        cfg.migrate_file(self.path)
        with open(self.path) as f:
            migrated = f.read()
        self.assertIs(cfg.migrate_file(self.path), False)
        with open(self.path) as f:
            self.assertEqual(f.read(), migrated)
        with open(self.path + ".v1.bak") as f:
            self.assertEqual(f.read(), self.V1_TEXT)

    def test_invalid_file_writes_nothing(self):
        text = '{"port": 70000}'
        self.write(text)
        with self.assertRaises(cfg.ConfigError):
            cfg.migrate_file(self.path)
        with open(self.path) as f:
            self.assertEqual(f.read(), text)
        self.assertFalse(os.path.exists(self.path + ".v1.bak"))


class Callers(Files):
    def test_connect_timeout_in_seconds(self):
        self.assertEqual(connect_args(self.load({"timeout": 2.5})),
                         {"address": ("localhost", 8080), "timeout": 2.5})
        self.assertEqual(connect_args(cfg.Settings(host="h", port=1, timeout_ms=250)),
                         {"address": ("h", 1), "timeout": 0.25})

    def test_no_timeout(self):
        self.assertIsNone(connect_args(self.load({"timeout": 0}))["timeout"])
        self.assertIsNone(connect_args(cfg.Settings(timeout_ms=None))["timeout"])

    def attempts(self, s):
        calls, sleeps = [], []

        def down():
            calls.append(1)
            raise OSError("down")

        with self.assertRaises(OSError):
            call_with_retry(s, down, sleep=sleeps.append)
        return len(calls), [round(x, 6) for x in sleeps]

    def test_attempts_same_as_v1(self):
        self.assertEqual(self.attempts(self.load({"retries": 2})), (3, [0.1, 0.2]))
        self.assertEqual(self.attempts(self.load({})), (1, []))
        self.assertEqual(self.attempts(cfg.Settings(max_attempts=4)), (4, [0.1, 0.2, 0.4]))

    def test_success_after_retries(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) < 2:
                raise OSError
            return "ok"

        self.assertEqual(call_with_retry(cfg.Settings(max_attempts=2), flaky, sleep=lambda s: None), "ok")

    def test_features(self):
        s = self.load({"features": "b, a,,b"})
        self.assertTrue(enabled(s, "a"))
        self.assertFalse(enabled(s, "c"))
        self.assertFalse(enabled(s, ""))
        self.assertEqual(all_enabled(s), ["a", "b"])
        self.assertEqual(all_enabled(cfg.Settings(features=["z", "y"])), ["y", "z"])

    def test_log_level(self):
        self.assertEqual(level(self.load({"log_level": "warning"})), logging.WARNING)
        self.assertEqual(level(cfg.Settings()), logging.INFO)


if __name__ == "__main__":
    unittest.main()
