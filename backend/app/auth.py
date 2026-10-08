"""Modular authentication for the AI Multi-Agent Career Analysis Platform.

Design notes
------------
* Mock, file-backed auth for development. It is fully swappable: routes only
  call the functions in this module, so replacing it with a real backend
  (DB + OAuth/JWT/IdP) never touches the UI or the page routes.
* Passwords are never stored in plain text — PBKDF2-HMAC-SHA256 with a random
  per-user salt (stdlib only, no new dependencies).
* Sessions are server-side random tokens persisted to JSON, delivered through
  an HttpOnly cookie. The JSON files live under ``app/data`` and are gitignored.
* No passwords, API keys or secrets are hardcoded anywhere.
"""

import hashlib
import hmac
import json
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

from . import config

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

SESSION_COOKIE = "ai_platform_session"
REMEMBER_DAYS = 30
DEFAULT_DAYS = 7
MIN_PASSWORD_LEN = 6
_PBKDF2_ITERATIONS = 260_000

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DATA_DIR: Path = config.DATA_DIR
USERS_FILE = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"

_lock = threading.RLock()


# ---------------------------------------------------------------------------
# Pydantic payloads (kept here so auth is self-contained)
# ---------------------------------------------------------------------------

class LoginIn(BaseModel):
    email: str
    password: str
    remember: bool = False


class SignupIn(BaseModel):
    full_name: str
    email: str
    password: str


class ForgotIn(BaseModel):
    email: str


# ---------------------------------------------------------------------------
# JSON persistence helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path: Path, data: Any) -> None:
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_users() -> dict:
    return _load_json(USERS_FILE, {})


def _load_sessions() -> dict:
    return _load_json(SESSIONS_FILE, {})


# ---------------------------------------------------------------------------
# Password handling (PBKDF2, stdlib only)
# ---------------------------------------------------------------------------

def _hash_password(password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
    """Return (salt_hex, password_hash_hex)."""
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return salt.hex(), digest.hex()


def _verify_password(password: str, salt_hex: str, expected_hash: str) -> bool:
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), _PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(digest.hex(), expected_hash)


# ---------------------------------------------------------------------------
# User store
# ---------------------------------------------------------------------------

def _public_user(record: dict) -> dict:
    return {
        "full_name": record.get("full_name", ""),
        "email": record.get("email", ""),
        "created": record.get("created"),
    }


def user_by_email(email: str) -> Optional[dict]:
    email = (email or "").strip().lower()
    return _load_users().get(email)


def create_user(full_name: str, email: str, password: str) -> dict:
    """Create a new account. Raises ValueError with a message on bad input."""
    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()
    if not full_name:
        raise ValueError("Full name is required.")
    if not _EMAIL_RE.match(email):
        raise ValueError("Enter a valid email address.")
    if len(password or "") < MIN_PASSWORD_LEN:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LEN} characters.")

    with _lock:
        users = _load_users()
        if email in users:
            raise ValueError("An account with this email already exists.")
        salt, digest = _hash_password(password)
        users[email] = {
            "full_name": full_name,
            "email": email,
            "salt": salt,
            "hash": digest,
            "created": datetime.now(timezone.utc).isoformat(),
        }
        _save_json(USERS_FILE, users)
        return _public_user(users[email])


def authenticate(email: str, password: str) -> Optional[dict]:
    email = (email or "").strip().lower()
    record = _load_users().get(email)
    if record and _verify_password(password or "", record.get("salt", ""), record.get("hash", "")):
        return _public_user(record)
    return None


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def create_session(email: str) -> str:
    email = (email or "").strip().lower()
    token = secrets.token_hex(32)
    with _lock:
        sessions = _load_sessions()
        sessions[token] = {
            "email": email,
            "created": datetime.now(timezone.utc).isoformat(),
        }
        _save_json(SESSIONS_FILE, sessions)
    return token


def user_by_token(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    record = _load_sessions().get(token)
    if not record:
        return None
    user = _load_users().get(record.get("email", ""))
    return _public_user(user) if user else None


def destroy_session(token: Optional[str]) -> None:
    if not token:
        return
    with _lock:
        sessions = _load_sessions()
        if token in sessions:
            del sessions[token]
            _save_json(SESSIONS_FILE, sessions)


def current_user(request) -> Optional[dict]:
    """Resolve the logged-in user from the request, or None."""
    return user_by_token(request.cookies.get(SESSION_COOKIE))


def session_max_age(remember: bool) -> int:
    """Cookie max-age in seconds."""
    return (REMEMBER_DAYS if remember else DEFAULT_DAYS) * 24 * 3600