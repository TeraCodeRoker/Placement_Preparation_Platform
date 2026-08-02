"""Auth crypto primitives: argon2 hashing, JWT, refresh tokens (framework-neutral)."""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from django.conf import settings

from apps.core.exceptions import UnauthorizedError

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    now = datetime.now(UTC)
    ttl = settings.JWT_ACCESS_TTL_MIN if expires_minutes is None else expires_minutes
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Wrong token type.")
    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)
