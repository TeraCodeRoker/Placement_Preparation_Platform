"""Auth + user endpoints (plain Django views)."""
from __future__ import annotations

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.cookies import (
    REFRESH_COOKIE,
    clear_auth_cookies,
    require_csrf,
    set_auth_cookies,
)
from apps.accounts.models import User
from apps.accounts.schemas import (
    ClaimRequest,
    ClaimResponse,
    GuestResponse,
    LoginRequest,
    ProfileResponse,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from apps.accounts.services import AuthService, TokenService
from apps.core.deps import require_user
from apps.core.exceptions import UnauthorizedError
from apps.core.json_api import json_response, parse_body
from apps.core.security import create_access_token, generate_csrf_token


def _issue_tokens(user: User) -> tuple[str, str]:
    """Return (access_token, raw_refresh_token)."""
    access = create_access_token(str(user.id), user.role)
    raw_refresh = TokenService().issue(user.id)
    return access, raw_refresh


@require_POST
def register(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, RegisterRequest)
    with transaction.atomic():
        user = AuthService().register(req.email, req.password)
        access, raw_refresh = _issue_tokens(user)
    resp = json_response(
        TokenResponse(access_token=access, user=UserOut.model_validate(user)), status=201
    )
    set_auth_cookies(resp, raw_refresh, generate_csrf_token())
    return resp


@require_POST
def login(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, LoginRequest)
    with transaction.atomic():
        user = AuthService().authenticate(req.email, req.password)
        access, raw_refresh = _issue_tokens(user)
    resp = json_response(TokenResponse(access_token=access, user=UserOut.model_validate(user)))
    set_auth_cookies(resp, raw_refresh, generate_csrf_token())
    return resp


@require_POST
def refresh(request: HttpRequest) -> HttpResponse:
    require_csrf(request)
    raw = request.COOKIES.get(REFRESH_COOKIE)
    if not raw:
        raise UnauthorizedError("Missing refresh token.")
    with transaction.atomic():
        new_raw, user_id = TokenService().rotate(raw)
        user = User.objects.filter(id=user_id).first()
        if user is None:
            raise UnauthorizedError("Account no longer exists.")
        access = create_access_token(str(user.id), user.role)
    resp = json_response(TokenResponse(access_token=access, user=UserOut.model_validate(user)))
    set_auth_cookies(resp, new_raw, generate_csrf_token())
    return resp


@require_POST
def logout(request: HttpRequest) -> HttpResponse:
    require_csrf(request)
    raw = request.COOKIES.get(REFRESH_COOKIE)
    if raw:
        TokenService().revoke(raw)
    resp = json_response({"status": "logged_out"})
    clear_auth_cookies(resp)
    return resp


@require_POST
def guest(request: HttpRequest) -> HttpResponse:
    guest_session = AuthService().create_guest()
    return json_response(
        GuestResponse(guest_token=guest_session.guest_token, expires_at=guest_session.expires_at),
        status=201,
    )


@require_POST
@require_user
def claim(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, ClaimRequest)
    with transaction.atomic():
        claimed = AuthService().claim_guest(request.current_user.id, req.guest_token)
    return json_response(ClaimResponse(claimed=claimed))


@require_http_methods(["GET", "DELETE"])
@require_user
def me(request: HttpRequest) -> HttpResponse:
    if request.method == "DELETE":
        with transaction.atomic():
            request.current_user.delete()
        return json_response({"status": "deleted"})
    return json_response(ProfileResponse.model_validate(request.current_user))
