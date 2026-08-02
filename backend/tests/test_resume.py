"""Resume endpoints (Gemini + PDF extraction mocked)."""
import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.resume import uploads

pytestmark = pytest.mark.django_db

BASE = "/api/v1/ai/resume"
_PAYLOADS = {
    "ResumeAnalysisSchema": {"overall_score": 88, "verdict": "Strong."},
    "AtsSchema": {"ats_score": 72, "will_pass_ats": True},
    "BulletSchema": {"improved": "Cut latency 40%"},
    "PdfJsonSchema": {"name": "Jane Doe", "skills": ["Python"]},
}


class FakeGemini:
    def generate_json(self, prompt, schema):
        return schema.model_validate(_PAYLOADS.get(schema.__name__, {}))


@pytest.fixture(autouse=True)
def _fake(monkeypatch):
    monkeypatch.setattr("apps.resume.views.get_gemini_service", lambda: FakeGemini())


def _post(client, url, payload=None, **extra):
    return client.post(
        url, data=json.dumps(payload or {}), content_type="application/json", **extra
    )


def _fake_pdf(text: str):
    class _Page:
        def extract_text(self):
            return text

    class _Pdf:
        pages = [_Page()]

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return lambda _stream: _Pdf()


def test_analyze(client: Client) -> None:
    resp = _post(client, f"{BASE}/analyze", {"resume_text": "t", "target_role": "SWE"})
    assert resp.status_code == 200 and resp.json()["overall_score"] == 88


def test_ats_and_bullet(client: Client) -> None:
    ats = _post(client, f"{BASE}/ats-score", {"resume_text": "r", "job_description": "jd"})
    assert ats.json()["ats_score"] == 72
    bullet = _post(client, f"{BASE}/improve-bullet", {"bullet": "did stuff"})
    assert bullet.json()["improved"]


def test_pdf_to_json(client: Client, monkeypatch) -> None:
    monkeypatch.setattr(uploads.pdfplumber, "open", _fake_pdf("Jane Doe resume " * 10))
    f = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 content", content_type="application/pdf")
    resp = client.post(f"{BASE}/pdf-to-json", {"file": f})
    assert resp.status_code == 200 and resp.json()["structured"]["name"] == "Jane Doe"


def test_non_pdf_rejected(client: Client) -> None:
    f = SimpleUploadedFile("evil.pdf", b"PK\x03\x04 not a pdf", content_type="application/pdf")
    resp = client.post(f"{BASE}/pdf-to-json", {"file": f})
    assert resp.status_code == 400 and resp.json()["error"]["code"] == "bad_request"


def test_history(client: Client) -> None:
    token = _post(
        client, "/api/v1/auth/register", {"email": "r@x.com", "password": "password123"}
    ).json()["access_token"]
    auth = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    _post(client, f"{BASE}/analyze", {"resume_text": "t", "target_role": "SWE"}, **auth)
    history = client.get(f"{BASE}/history", **auth)
    assert history.status_code == 200 and history.json()[0]["kind"] == "analyze"
