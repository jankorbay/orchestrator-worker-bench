"""Request handlers for the internal reporting service."""
import base64
import hashlib
import html
import os
import pickle
import secrets
import sqlite3
import subprocess

UPLOAD_DIR = "/srv/uploads"
AVATAR_DIR = "/srv/avatars"
SORT_COLUMNS = {"date": "created_at", "total": "total_cents"}


def get_user(db: sqlite3.Connection, username: str):
    query = f"SELECT id, username, email FROM users WHERE username = '{username}'"
    return db.execute(query).fetchone()


def list_orders(db: sqlite3.Connection, user_id: int, sort: str = "date"):
    column = SORT_COLUMNS.get(sort, "created_at")
    return db.execute(
        f"SELECT id, total_cents FROM orders WHERE user_id = ? ORDER BY {column}",
        (user_id,),
    ).fetchall()


def download_file(filename: str) -> bytes:
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "rb") as f:
        return f.read()


def avatar_path(name: str) -> str:
    base = os.path.realpath(AVATAR_DIR)
    path = os.path.realpath(os.path.join(base, name))
    if not path.startswith(base + os.sep):
        raise PermissionError("invalid avatar name")
    return path


def run_report(report_name: str) -> str:
    result = subprocess.run(
        f"/opt/reports/bin/generate --name {report_name}",
        shell=True, capture_output=True, text=True, check=True,
    )
    return result.stdout


def export_csv(table: str) -> str:
    if table not in {"orders", "users"}:
        raise ValueError("unknown table")
    result = subprocess.run(
        ["/opt/reports/bin/export", "--table", table],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def load_session(cookie_value: str) -> dict:
    return pickle.loads(base64.b64decode(cookie_value))


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


def check_api_key(given: str, expected: str) -> bool:
    return secrets.compare_digest(given.encode(), expected.encode())


def new_reset_token() -> str:
    return secrets.token_urlsafe(32)


def render_greeting(display_name: str) -> str:
    return f"<p>Welcome back, {html.escape(display_name)}!</p>"
