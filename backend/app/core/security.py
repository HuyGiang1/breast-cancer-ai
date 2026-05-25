import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import Header, HTTPException

from app.core.database import db


UTC = timezone.utc


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        120_000,
    )
    encoded = base64.b64encode(digest).decode("ascii")
    return f"{salt_value}${encoded}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, stored = password_hash.split("$", 1)
    except ValueError:
        return False
    computed = hash_password(password, salt=salt).split("$", 1)[1]
    return hmac.compare_digest(stored, computed)


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_password_reset_token() -> str:
    return secrets.token_urlsafe(24)


def _fetch_session_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    token = authorization[len(prefix):].strip()
    return token or None


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    token = _fetch_session_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    row = db.fetch_one(
        """
        SELECT users.id, users.email, users.full_name, users.is_active, sessions.expires_at
             , users.role
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ?
        """,
        (token,),
    )
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid session token")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Session expired")

    if not bool(row["is_active"]):
        raise HTTPException(status_code=403, detail="User is inactive")

    return {
        "id": int(row["id"]),
        "email": str(row["email"]),
        "full_name": str(row["full_name"]),
        "role": str(row["role"] or "user"),
    }


def get_optional_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    token = _fetch_session_token(authorization)
    if not token:
        return None
    try:
        return get_current_user(authorization)
    except HTTPException:
        return None
