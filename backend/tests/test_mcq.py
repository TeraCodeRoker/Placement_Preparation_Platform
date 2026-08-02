"""MCQ generation (cache-first), daily, attempt, history (Gemini mocked)."""
import json

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

GENERATE = "/api/v1/ai/mcq/generate"
DAILY = "/api/v1/ai/mcq/daily-challenge"
ATTEMPT = "/api/v1/ai/mcq/attempt"
HISTORY = "/api/v1/ai/mcq/history"


class FakeGemini:
    def __init__(self) -> None:
        self.calls = 0

    def generate_json(self, prompt: str, schema: type):
        self.calls += 1
        if schema.__name__ == "DailyChallengeSchema":
            return schema.model_validate(
                {
                    "question": "Daily?",
                    "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
                    "correct_answer": "B",
                    "explanation": "e",
                    "fun_fact": "did you know",
                }
            )
        return schema.model_validate(
            {
                "questions": [
                    {
                        "question": f"Q{i}",
                        "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
                        "correct_answer": "A",
                        "explanation": "x",
                    }
                    for i in range(3)
                ]
            }
        )


FAKE = FakeGemini()


@pytest.fixture(autouse=True)
def _fake(monkeypatch):
    FAKE.calls = 0
    monkeypatch.setattr("apps.mcq.views.get_gemini_service", lambda: FAKE)


def _post(client, url, payload=None, **extra):
    return client.post(
        url, data=json.dumps(payload or {}), content_type="application/json", **extra
    )


def test_generate_is_cache_first(client: Client) -> None:
    first = _post(client, GENERATE, {"topic": "OS", "count": 3, "difficulty": "easy"})
    assert first.status_code == 200
    assert len(first.json()["questions"]) == 3
    assert FAKE.calls == 1
    second = _post(client, GENERATE, {"topic": "OS", "count": 3, "difficulty": "easy"})
    assert FAKE.calls == 1  # cache hit — no second Gemini call
    assert second.json()["set_id"] == first.json()["set_id"]


def test_daily_folds_fun_fact(client: Client) -> None:
    resp = _post(client, DAILY, {"topic": "networks"})
    assert resp.status_code == 200
    assert "did you know" in resp.json()["explanation"]


def test_attempt_and_history(client: Client) -> None:
    token = _post(
        client, "/api/v1/auth/register", {"email": "m@x.com", "password": "password123"}
    ).json()["access_token"]
    auth = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    attempt = _post(
        client, ATTEMPT, {"subject": "OS", "difficulty": "medium", "correct": 4, "total": 5}, **auth
    )
    assert attempt.json()["percent"] == 80
    history = client.get(HISTORY, **auth)
    assert len(history.json()) == 1


def test_history_requires_auth(client: Client) -> None:
    assert client.get(HISTORY).status_code == 401


def test_oversized_count_rejected(client: Client) -> None:
    assert _post(client, GENERATE, {"topic": "OS", "count": 99}).status_code == 422
