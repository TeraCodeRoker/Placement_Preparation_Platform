"""Interview lifecycle, history, code-review, idempotency (Gemini mocked)."""
import json

import pytest
from django.test import Client

from apps.interview.models import InterviewResult

pytestmark = pytest.mark.django_db

START = "/api/v1/ai/interview/start"
ANSWER = "/api/v1/ai/interview/answer"
HISTORY = "/api/v1/ai/interview/history"
CODE_REVIEW = "/api/v1/ai/interview/code-review"


class FakeGemini:
    def generate_text(self, prompt: str) -> str:
        return "Generated question or review."

    def generate_json(self, prompt: str, schema: type):
        return schema(score=8, feedback="Solid.", correct_answer="Ideal.")


@pytest.fixture(autouse=True)
def _fake_gemini(monkeypatch):
    monkeypatch.setattr("apps.interview.views.get_gemini_service", lambda: FakeGemini())


def _post(client: Client, url: str, payload: dict | None = None, **extra: str):
    return client.post(
        url, data=json.dumps(payload or {}), content_type="application/json", **extra
    )


def test_full_lifecycle(client: Client) -> None:
    start = _post(client, START, {"num_subjective": 1, "num_dsa": 1})
    assert start.status_code == 200
    sid = start.json()["session_id"]
    assert start.json()["question"]["total_questions"] == 2

    a1 = _post(client, ANSWER, {"session_id": sid, "answer": "first"})
    assert a1.json()["is_complete"] is False
    assert a1.json()["next_question"]["question_number"] == 2

    a2 = _post(client, ANSWER, {"session_id": sid, "answer": "second"})
    assert a2.json()["is_complete"] is True
    assert a2.json()["summary"]["total_questions"] == 2


def test_answer_unknown_session_404(client: Client) -> None:
    resp = _post(
        client, ANSWER,
        {"session_id": "00000000-0000-0000-0000-000000000000", "answer": "x"},
    )
    assert resp.status_code == 404


def test_idempotent_answer(client: Client) -> None:
    sid = _post(client, START, {"num_subjective": 1, "num_dsa": 1}).json()["session_id"]
    _post(client, ANSWER, {"session_id": sid, "answer": "x", "idempotency_key": "k1"})
    _post(client, ANSWER, {"session_id": sid, "answer": "x", "idempotency_key": "k1"})
    assert InterviewResult.objects.count() == 1  # not double-counted


def test_history_requires_auth(client: Client) -> None:
    assert client.get(HISTORY).status_code == 401


def test_history_only_callers_sessions(client: Client) -> None:
    token = _post(
        client, "/api/v1/auth/register", {"email": "h@x.com", "password": "password123"}
    ).json()["access_token"]
    auth = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    _post(client, START, {"num_subjective": 1, "num_dsa": 0}, **auth)
    _post(client, START, {"num_subjective": 1, "num_dsa": 0})  # anonymous
    resp = client.get(HISTORY, **auth)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_code_review(client: Client) -> None:
    resp = _post(
        client, CODE_REVIEW,
        {"question": "Two Sum", "user_code": "print(1)", "language": "python"},
    )
    assert resp.status_code == 200
    assert resp.json()["review"]
    assert resp.json()["language"] == "python"
