"""Auth orchestration + refresh-token lifecycle (sync, Django ORM)."""
from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import GuestSession, RefreshToken, User
from apps.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from apps.core.security import (
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

# Aggregates carrying guest_id, re-parented on account claim.
_CLAIMABLE = [
    ("apps.interview.models", "InterviewSession", "interview_sessions"),
    ("apps.mcq.models", "McqAttempt", "mcq_attempts"),
    ("apps.resume.models", "ResumeAnalysis", "resume_analyses"),
    ("apps.oa.models", "OASubmission", "oa_submissions"),
]


class AuthService:
    def register(self, email: str, password: str) -> User:
        if User.objects.filter(email=email).exists():
            raise ConflictError("An account with this email already exists.")
        bootstrap = settings.ADMIN_BOOTSTRAP_EMAIL.strip().lower()
        role = "admin" if bootstrap and email.lower() == bootstrap else "user"
        return User.objects.create(
            email=email, hashed_password=hash_password(password), role=role
        )

    def authenticate(self, email: str, password: str) -> User:
        user = User.objects.filter(email=email).first()
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")
        return user

    def create_guest(self) -> GuestSession:
        return GuestSession.objects.create(
            guest_token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(days=settings.GUEST_TTL_DAYS),
        )

    def claim_guest(self, user_id: uuid.UUID, guest_token: str) -> dict[str, int]:
        from importlib import import_module

        guest = GuestSession.objects.filter(guest_token=guest_token).first()
        if guest is None:
            raise NotFoundError("Guest session not found or already expired.")
        claimed: dict[str, int] = {}
        for module_path, class_name, table in _CLAIMABLE:
            model = getattr(import_module(module_path), class_name)
            claimed[table] = model.objects.filter(guest_id=guest.id).update(
                user_id=user_id, guest_id=None
            )
        return claimed


class TokenService:
    def issue(self, user_id: uuid.UUID) -> str:
        raw = generate_refresh_token()
        RefreshToken.objects.create(
            user_id=user_id,
            token_hash=hash_refresh_token(raw),
            expires_at=timezone.now() + timedelta(days=settings.JWT_REFRESH_TTL_DAYS),
            revoked=False,
        )
        return raw

    def rotate(self, raw_token: str) -> tuple[str, uuid.UUID]:
        record = RefreshToken.objects.filter(token_hash=hash_refresh_token(raw_token)).first()
        if record is None or record.revoked or record.expires_at < timezone.now():
            raise UnauthorizedError("Refresh token is invalid or has been revoked.")
        record.revoked = True
        record.save(update_fields=["revoked"])
        return self.issue(record.user_id), record.user_id

    def revoke(self, raw_token: str) -> None:
        RefreshToken.objects.filter(token_hash=hash_refresh_token(raw_token)).update(revoked=True)
