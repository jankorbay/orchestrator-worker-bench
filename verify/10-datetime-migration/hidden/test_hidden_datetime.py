import pathlib
import re
import time
import unittest
from datetime import datetime, timedelta, timezone

from authsvc import audit, cleanup, quota, scheduler, sessions, timeutil, tokens
from authsvc.models import User

UTC = timezone.utc
WIRE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
AUDIT = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d{6})?Z$")
DB = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$")


def now():
    return datetime.now(UTC)


class Base(unittest.TestCase):
    def assertAwareUtc(self, value):
        self.assertIsInstance(value, datetime)
        self.assertIsNotNone(value.tzinfo, f"{value!r} is naive")
        self.assertEqual(value.utcoffset(), timedelta(0))

    def assertNear(self, value, expected, seconds=5):
        self.assertLessEqual(abs((value - expected).total_seconds()), seconds)


class NoDeprecatedCalls(unittest.TestCase):
    def test_no_utcnow_or_utcfromtimestamp_left(self):
        root = pathlib.Path(__file__).resolve().parent
        offenders = [str(p.relative_to(root)) for p in root.rglob("*.py") if p.name != pathlib.Path(__file__).name
                     and re.search(r"utcnow|utcfromtimestamp", p.read_text())]
        self.assertEqual(offenders, [])


class TimeUtil(Base):
    def test_wire_roundtrip_is_aware(self):
        parsed = timeutil.from_wire("2026-10-09T12:00:00Z")
        self.assertAwareUtc(parsed)
        self.assertEqual(parsed, datetime(2026, 10, 9, 12, tzinfo=UTC))
        self.assertEqual(timeutil.to_wire(parsed), "2026-10-09T12:00:00Z")

    def test_unix(self):
        when = datetime(2026, 10, 9, 12, 0, 5, tzinfo=UTC)
        self.assertEqual(timeutil.to_unix(when), int(when.timestamp()))
        self.assertEqual(timeutil.from_unix(0), datetime(1970, 1, 1, tzinfo=UTC))
        self.assertAwareUtc(timeutil.from_unix(1_790_000_000))

    def test_utc_today(self):
        self.assertIn(timeutil.utc_today(), {now().date().isoformat(), (now() - timedelta(seconds=5)).date().isoformat()})


class Sessions(Base):
    def test_create_format_and_ttl(self):
        s = sessions.create_session(1)
        self.assertRegex(s["created"], WIRE)
        self.assertRegex(s["expires"], WIRE)
        created, expires = timeutil.from_wire(s["created"]), timeutil.from_wire(s["expires"])
        self.assertEqual(expires - created, timedelta(hours=12))
        self.assertNear(created, now())

    def test_is_expired_with_explicit_aware_now(self):
        s = {"expires": "2026-10-09T12:00:00Z"}
        self.assertFalse(sessions.is_expired(s, datetime(2026, 10, 9, 11, 59, tzinfo=UTC)))
        self.assertTrue(sessions.is_expired(s, datetime(2026, 10, 9, 12, 0, tzinfo=UTC)))

    def test_is_expired_default_now(self):
        self.assertTrue(sessions.is_expired({"expires": "2000-01-01T00:00:00Z"}))
        self.assertFalse(sessions.is_expired(sessions.create_session(1)))

    def test_refresh_and_remaining(self):
        s = sessions.refresh({"id": "x", "user_id": 1, "created": "2000-01-01T00:00:00Z",
                              "expires": "2000-01-01T00:00:00Z"})
        self.assertRegex(s["expires"], WIRE)
        left = sessions.remaining(s)
        self.assertIsInstance(left, timedelta)
        self.assertNear(now() + left, now() + timedelta(hours=12))


class Tokens(Base):
    def test_issue_timestamps(self):
        payload = tokens.verify(tokens.issue(3, ["read"]))
        self.assertEqual(payload["exp"] - payload["iat"], 900)
        self.assertLessEqual(abs(payload["iat"] - time.time()), 5)

    def test_expired_token_rejected(self):
        past = timeutil.to_unix(now() - timedelta(minutes=1))
        self.assertIsNone(tokens.verify(tokens.encode({"sub": 3, "scopes": [], "iat": past - 900, "exp": past})))

    def test_expires_at(self):
        token = tokens.issue(3, ["read"])
        when = tokens.expires_at(token)
        self.assertAwareUtc(when)
        self.assertNear(when, now() + timedelta(minutes=15))


class Audit(Base):
    def setUp(self):
        audit.clear()

    def test_timestamp_format_unchanged(self):
        entry = audit.record("ada", "login", ip="10.0.0.1")
        self.assertRegex(entry["ts"], AUDIT)
        self.assertNear(datetime.fromisoformat(entry["ts"][:-1]).replace(tzinfo=UTC), now())

    def test_entries_since(self):
        audit.record("ada", "login")
        self.assertEqual(len(audit.entries_since(now() - timedelta(minutes=1))), 1)
        self.assertEqual(audit.entries_since(now() + timedelta(minutes=1)), [])


class Models(Base):
    def test_created_at_is_aware(self):
        user = User(1, "ada@example.com")
        self.assertAwareUtc(user.created_at)
        self.assertNear(user.created_at, now())

    def test_login_and_age(self):
        user = User(1, "ada@example.com", created_at=now() - timedelta(days=3, hours=1))
        user.login()
        self.assertAwareUtc(user.last_login)
        self.assertEqual(user.account_age_days(), 3)


class Cleanup(Base):
    def test_expired_rows(self):
        old = (now() - timedelta(days=31)).strftime("%Y-%m-%d %H:%M:%S")
        fresh = (now() - timedelta(days=29)).strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(cleanup.expired_rows([{"id": 1, "updated": old}, {"id": 2, "updated": fresh}]), [1])

    def test_cutoff_string(self):
        text = cleanup.cutoff_string(30)
        self.assertRegex(text, DB)
        self.assertNear(datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC), now() - timedelta(days=30))


class Quota(Base):
    def test_key_format(self):
        self.assertRegex(quota.quota_key(9), r"^9:\d{4}-\d\d-\d\d$")
        self.assertTrue(quota.hit(9, limit=1000))

    def test_reset_time_is_next_utc_midnight(self):
        reset = quota.reset_time()
        self.assertAwareUtc(reset)
        self.assertEqual((reset.hour, reset.minute, reset.second), (0, 0, 0))
        self.assertTrue(timedelta(0) < reset - now() <= timedelta(days=1))


class Scheduler(Base):
    def test_next_daily_run(self):
        at = datetime(2026, 10, 9, 13, 30, tzinfo=UTC)
        self.assertEqual(scheduler.next_daily_run(14, at), datetime(2026, 10, 9, 14, tzinfo=UTC))
        self.assertEqual(scheduler.next_daily_run(13, at), datetime(2026, 10, 10, 13, tzinfo=UTC))

    def test_default_now_and_seconds_until(self):
        run = scheduler.next_daily_run(3)
        self.assertAwareUtc(run)
        self.assertTrue(0 < scheduler.seconds_until(run) <= 86400)


if __name__ == "__main__":
    unittest.main()
