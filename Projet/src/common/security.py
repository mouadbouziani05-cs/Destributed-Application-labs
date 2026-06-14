from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from src.common.errors import AuthenticationError


def hash_password(password: str) -> str:
    if not password:
        raise AuthenticationError("Password missing")
    salted = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return salted.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    *,
    user_id: int,
    username: str,
    role: str,
    secret: str,
    algorithm: str = "HS256",
    expires_minutes: int = 30,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "iss": "phishing-platform",
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(token: str, *, secret: str, algorithm: str = "HS256") -> dict[str, Any]:
    try:
        decoded = jwt.decode(token, secret, algorithms=[algorithm], options={"require": ["sub", "username", "role", "exp"]})
        return decoded
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid token") from exc


def token_preview(token: str) -> str:
    if len(token) <= 12:
        return "***"
    return f"{token[:8]}...{token[-4:]}"
