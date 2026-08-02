"""Notes public listing + admin gating (admin via ADMIN_BOOTSTRAP_EMAIL)."""
import json

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

PUBLIC = "/api/v1/notes"
ADMIN = "/api/v1/admin/notes"


def _post(client, url, payload=None, **extra):
    return client.post(
        url, data=json.dumps(payload or {}), content_type="application/json", **extra
    )


def _admin(client, settings) -> dict:
    settings.ADMIN_BOOTSTRAP_EMAIL = "admin@x.com"
    token = _post(
        client, "/api/v1/auth/register", {"email": "admin@x.com", "password": "password123"}
    ).json()["access_token"]
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_public_lists_only_approved(client: Client, settings) -> None:
    admin = _admin(client, settings)
    _post(client, ADMIN, {"title": "Approved", "subject": "OS", "content_or_url": "x",
                          "approved": True}, **admin)
    _post(client, ADMIN, {"title": "Pending", "subject": "OS", "content_or_url": "y",
                          "approved": False}, **admin)
    assert [n["title"] for n in client.get(PUBLIC).json()] == ["Approved"]
    assert len(client.get(ADMIN, **admin).json()) == 2


def test_non_admin_cannot_upload(client: Client) -> None:
    token = _post(
        client, "/api/v1/auth/register", {"email": "u@x.com", "password": "password123"}
    ).json()["access_token"]
    resp = _post(client, ADMIN, {"title": "x", "content_or_url": "y"},
                 HTTP_AUTHORIZATION=f"Bearer {token}")
    assert resp.status_code == 403


def test_anonymous_cannot_upload(client: Client) -> None:
    assert _post(client, ADMIN, {"title": "x", "content_or_url": "y"}).status_code == 401


def test_approve_publishes(client: Client, settings) -> None:
    admin = _admin(client, settings)
    created = _post(
        client, ADMIN, {"title": "N", "content_or_url": "z", "approved": False}, **admin
    )
    note_id = created.json()["id"]
    assert client.get(PUBLIC).json() == []
    client.patch(
        f"{ADMIN}/{note_id}", data=json.dumps({"approved": True}),
        content_type="application/json", **admin,
    )
    assert len(client.get(PUBLIC).json()) == 1
