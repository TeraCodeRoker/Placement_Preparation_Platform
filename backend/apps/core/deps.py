"""Auth guards as view decorators + optional-identity resolver (replaces Depends).

- ``@require_user`` / ``@require_admin`` set ``request.current_user`` or raise
  401/403.
- ``get_identity(request)`` resolves user (Bearer) / guest (X-Guest-Token) /
  anonymous and never raises — so guest mode always works on AI endpoints.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest, HttpResponse

from apps.core.exceptions import ForbiddenError, UnauthorizedError
from apps.core.security import decode_access_token

View = Callable[..., HttpResponse]


class Identity:
    def __init__(self, user: Any | None = None, guest: Any | None = None) -> None:
        self.user = user
        self.guest = guest

    @property
    def user_id(self) -> uuid.UUID | None:
        return self.user.id if self.user is not None else None

    @property
    def guest_id(self) -> uuid.UUID | None:
        return self.guest.id if self.guest is not None else None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None


def _bearer(request: HttpRequest) -> str:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header.")
    return header[len("Bearer ") :]


def _current_user(request: HttpRequest) -> Any:
    from apps.accounts.models import User

    payload = decode_access_token(_bearer(request))
    user = User.objects.filter(id=uuid.UUID(payload["sub"])).first()
    if user is None:
        raise UnauthorizedError("Account not found.")
    return user


def require_user(view: View) -> View:
    @wraps(view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        request.current_user = _current_user(request)  # type: ignore[attr-defined]
        return view(request, *args, **kwargs)

    return wrapper


def require_admin(view: View) -> View:
    @wraps(view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user = _current_user(request)
        if user.role != "admin":
            raise ForbiddenError("Administrator access required.")
        request.current_user = user  # type: ignore[attr-defined]
        return view(request, *args, **kwargs)

    return wrapper


def get_identity(request: HttpRequest) -> Identity:
    from apps.accounts.models import GuestSession, User

    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        try:
            payload = decode_access_token(header[len("Bearer ") :])
            user = User.objects.filter(id=uuid.UUID(payload["sub"])).first()
            if user is not None:
                return Identity(user=user)
        except UnauthorizedError:
            pass
    guest_token = request.headers.get("X-Guest-Token")
    if guest_token:
        guest = GuestSession.objects.filter(guest_token=guest_token).first()
        if guest is not None:
            return Identity(guest=guest)
    return Identity()
