"""Auth aggregate: user, guest session, refresh token."""
from __future__ import annotations

import uuid

from django.db import models


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=320, unique=True)
    hashed_password = models.CharField(max_length=255)
    role = models.CharField(max_length=16, default="user")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"


class GuestSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest_token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "guest_sessions"


class RefreshToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "refresh_tokens"
