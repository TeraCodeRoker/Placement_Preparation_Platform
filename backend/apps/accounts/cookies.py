"""Auth cookie helpers + double-submit CSRF (ADR-004)."""
from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from apps.core.exceptions import ForbiddenError

REFRESH_COOKIE = "prepstack_refresh"
CSRF_COOKIE = "prepstack_csrf"
REFRESH_PATH = "/api/v1/auth"


def _secure() -> bool:
    return settings.APP_ENV != "local"


def set_auth_cookies(response: HttpResponse, refresh_token: str, csrf_token: str) -> None:
    max_age = settings.JWT_REFRESH_TTL_DAYS * 86400
    secure = _secure()
    response.set_cookie(
        REFRESH_COOKIE, refresh_token, max_age=max_age, httponly=True,
        secure=secure, samesite="Lax", path=REFRESH_PATH,
    )
    response.set_cookie(
        CSRF_COOKIE, csrf_token, max_age=max_age, httponly=False,
        secure=secure, samesite="Lax", path="/",
    )


def clear_auth_cookies(response: HttpResponse) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH)
    response.delete_cookie(CSRF_COOKIE, path="/")


def require_csrf(request: HttpRequest) -> None:
    cookie = request.COOKIES.get(CSRF_COOKIE)
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or cookie != header:
        raise ForbiddenError("CSRF validation failed.")
