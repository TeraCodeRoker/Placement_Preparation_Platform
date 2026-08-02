"""Auth lifecycle over HTTP (Django test client)."""
import json

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

CREDS = {"email": "cand@example.com", "password": "password123"}


def _post(client: Client, url: str, payload: dict | None = None, **extra: str):
    return client.post(
        url, data=json.dumps(payload or {}), content_type="application/json", **extra
    )


def test_register_sets_cookies_and_returns_access(client: Client) -> None:
    resp = _post(client, "/api/v1/auth/register", CREDS)
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["email"] == CREDS["email"]
    assert body["user"]["role"] == "user"
    assert "prepstack_refresh" in resp.cookies
    assert "prepstack_csrf" in resp.cookies


def test_duplicate_email_conflicts(client: Client) -> None:
    _post(client, "/api/v1/auth/register", CREDS)
    resp = _post(client, "/api/v1/auth/register", CREDS)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


def test_login_wrong_password_unauthorized(client: Client) -> None:
    _post(client, "/api/v1/auth/register", CREDS)
    resp = _post(client, "/api/v1/auth/login", {**CREDS, "password": "wrong"})
    assert resp.status_code == 401


def test_refresh_rotates_with_csrf(client: Client) -> None:
    _post(client, "/api/v1/auth/register", CREDS)
    csrf = client.cookies["prepstack_csrf"].value
    old_refresh = client.cookies["prepstack_refresh"].value
    resp = client.post("/api/v1/auth/refresh", HTTP_X_CSRF_TOKEN=csrf)
    assert resp.status_code == 200
    assert resp.json()["access_token"]
    assert client.cookies["prepstack_refresh"].value != old_refresh


def test_refresh_without_csrf_forbidden(client: Client) -> None:
    _post(client, "/api/v1/auth/register", CREDS)
    resp = client.post("/api/v1/auth/refresh")
    assert resp.status_code == 403


def test_logout_then_refresh_fails(client: Client) -> None:
    _post(client, "/api/v1/auth/register", CREDS)
    csrf = client.cookies["prepstack_csrf"].value
    assert client.post("/api/v1/auth/logout", HTTP_X_CSRF_TOKEN=csrf).status_code == 200
    resp = client.post("/api/v1/auth/refresh", HTTP_X_CSRF_TOKEN=csrf)
    assert resp.status_code in (401, 403)


def test_guest_issues_token(client: Client) -> None:
    resp = _post(client, "/api/v1/auth/guest")
    assert resp.status_code == 201
    assert resp.json()["guest_token"]


def test_me_and_delete(client: Client) -> None:
    token = _post(client, "/api/v1/auth/register", CREDS).json()["access_token"]
    auth = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    me = client.get("/api/v1/users/me", **auth)
    assert me.status_code == 200
    assert me.json()["email"] == CREDS["email"]

    deleted = client.delete("/api/v1/users/me", **auth)
    assert deleted.status_code == 200
    # Token still decodes but the user is gone -> 401.
    assert client.get("/api/v1/users/me", **auth).status_code == 401


def test_me_requires_auth(client: Client) -> None:
    assert client.get("/api/v1/users/me").status_code == 401
