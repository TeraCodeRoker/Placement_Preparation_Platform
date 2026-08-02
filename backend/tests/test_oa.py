"""OA lifecycle, degraded mode, 404 (Gemini + executor mocked)."""
import json

import pytest
from django.test import Client

from apps.integrations.execution.base import ExecutionResult
from apps.integrations.execution.errors import ExecutionUnavailableError

pytestmark = pytest.mark.django_db

BASE = "/api/v1/ai/oa"
_PROBLEM = {
    "title": "Sum",
    "statement": "Add numbers",
    "starter_code": {"python": "# code"},
    "visible_tests": [
        {"stdin": "a", "expected_output": "1"},
        {"stdin": "b", "expected_output": "2"},
    ],
    "hidden_tests": [
        {"stdin": "c", "expected_output": "3"},
        {"stdin": "d", "expected_output": "4"},
    ],
    "time_complexity_hint": "O(n)",
}
_REVIEW = {"correctness_rationale": "ok", "review_score": 8, "suggestions": []}


class FakeGemini:
    def generate_json(self, prompt, schema):
        if schema.__name__ == "OAReviewSchema":
            return schema.model_validate(_REVIEW)
        return schema.model_validate(_PROBLEM)


class FakeExecutor:
    def __init__(self, by_stdin):
        self.by_stdin = by_stdin

    def execute(self, language, source_code, stdin, timeout_s):
        return ExecutionResult(stdout=self.by_stdin.get(stdin, ""))


class RaisingExecutor:
    def execute(self, *a, **k):
        raise ExecutionUnavailableError()


def _install(monkeypatch, executor):
    monkeypatch.setattr("apps.oa.views.get_gemini_service", lambda: FakeGemini())
    monkeypatch.setattr("apps.oa.views.get_execution_provider", lambda: executor)


def _post(client, url, payload=None, **extra):
    return client.post(
        url, data=json.dumps(payload or {}), content_type="application/json", **extra
    )


def test_full_lifecycle(client: Client, monkeypatch) -> None:
    _install(monkeypatch, FakeExecutor({"a": "1", "b": "2", "c": "3", "d": "4"}))
    problem = _post(client, f"{BASE}/problem", {"step": "Step 3", "topic": "Two Sum"})
    assert problem.status_code == 200
    pid = problem.json()["problem_id"]
    assert len(problem.json()["visible_tests"]) == 2

    run = _post(
        client, f"{BASE}/run", {"problem_id": pid, "language": "python", "source_code": "x"}
    )
    assert run.json()["passed"] == 2 and run.json()["total"] == 2

    submit = _post(
        client, f"{BASE}/submit", {"problem_id": pid, "language": "python", "source_code": "x"}
    )
    body = submit.json()
    assert body["pass_count"] == 4 and body["total_count"] == 4
    assert body["final_score"] == 100 and body["mode"] == "graded"
    assert body["ai_review"]["review_score"] == 8
    # Hidden cases don't leak their I/O.
    hidden = [r for r in body["test_results"] if not r["visible"]]
    assert all(r["stdout"] is None and r["expected_output"] is None for r in hidden)

    got = client.get(f"{BASE}/submission/{body['submission_id']}")
    assert got.status_code == 200 and got.json()["final_score"] == 100


def test_degraded_mode(client: Client, monkeypatch) -> None:
    _install(monkeypatch, RaisingExecutor())
    pid = _post(client, f"{BASE}/problem", {"step": "S", "topic": "T"}).json()["problem_id"]
    submit = _post(
        client, f"{BASE}/submit", {"problem_id": pid, "language": "python", "source_code": "x"}
    )
    body = submit.json()
    assert body["mode"] == "ai_review_only"
    assert body["final_score"] == 0 and body["ai_review"] is not None


def test_run_unknown_problem_404(client: Client, monkeypatch) -> None:
    _install(monkeypatch, FakeExecutor({}))
    resp = _post(
        client, f"{BASE}/run",
        {
            "problem_id": "00000000-0000-0000-0000-000000000000",
            "language": "python",
            "source_code": "x",
        },
    )
    assert resp.status_code == 404
