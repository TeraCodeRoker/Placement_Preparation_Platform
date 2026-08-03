"""Gemini reliability (failure modes) + execution provider (sync)."""
import httpx
import pytest
from pydantic import BaseModel

from apps.integrations.execution.errors import (
    ExecutionUnavailableError,
    SubmissionTooLargeError,
    UnsupportedLanguageError,
)
from apps.integrations.execution.judge0 import Judge0ExecutionProvider
from apps.integrations.execution.paiza import PaizaExecutionProvider
from apps.integrations.execution.piston import PistonExecutionProvider
from apps.integrations.gemini.client import _is_gemini_compatible
from apps.integrations.gemini.errors import (
    GeminiEmptyResponseError,
    GeminiMalformedResponseError,
    GeminiSchemaViolationError,
    GeminiUnavailableError,
)
from apps.integrations.gemini.reliability import CircuitBreaker
from apps.integrations.gemini.service import GeminiService


class Sample(BaseModel):
    x: int


class _Returns:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def generate(self, prompt, *, response_schema=None):
        self.calls += 1
        return self.text


class _Raises:
    def __init__(self):
        self.calls = 0

    def generate(self, *a, **k):
        self.calls += 1
        raise ConnectionError("provider down")


class _FailsOnce:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def generate(self, *a, **k):
        self.calls += 1
        if self.calls == 1:
            raise ConnectionError("transient")
        return self.text


def _svc(client, **kw):
    kw.setdefault("max_retries", 0)
    kw.setdefault("backoff_base_s", 0)
    kw.setdefault("jitter_s", 0)
    return GeminiService(client, **kw)


# --- Gemini failure modes (§10.6) ---
def test_network_or_timeout_unavailable_503():
    with pytest.raises(GeminiUnavailableError) as e:
        _svc(_Raises()).generate_json("p", Sample)
    assert e.value.status_code == 503


def test_malformed_json_502():
    with pytest.raises(GeminiMalformedResponseError) as e:
        _svc(_Returns("not json")).generate_json("p", Sample)
    assert e.value.status_code == 502


def test_empty_response_502():
    with pytest.raises(GeminiEmptyResponseError):
        _svc(_Returns("  ")).generate_json("p", Sample)


def test_schema_violation_502():
    with pytest.raises(GeminiSchemaViolationError):
        _svc(_Returns('{"y": 1}')).generate_json("p", Sample)


def test_open_circuit_fast_fails():
    client = _Raises()
    service = _svc(client, breaker=CircuitBreaker(fail_threshold=1))
    with pytest.raises(GeminiUnavailableError):
        service.generate_text("p")
    assert client.calls == 1
    with pytest.raises(GeminiUnavailableError):
        service.generate_text("p")
    assert client.calls == 1  # breaker open — provider not hit again


def test_happy_and_retry():
    assert _svc(_Returns('```json\n{"x": 5}\n```')).generate_json("p", Sample) == Sample(x=5)
    client = _FailsOnce('{"x": 7}')
    assert _svc(client, max_retries=1).generate_json("p", Sample) == Sample(x=7)
    assert client.calls == 2


# --- Execution provider ---
def _provider(handler, max_bytes=64 * 1024):
    return Judge0ExecutionProvider(
        "https://judge0", "key", "host", max_bytes, transport=httpx.MockTransport(handler)
    )


def test_execution_success():
    def h(req):
        return httpx.Response(
            200,
            json={
                "stdout": "5\n",
                "status": {"id": 3, "description": "Accepted"},
                "time": "0.01",
            },
        )

    r = _provider(h).execute("python", "print(5)", "", 2.0)
    assert r.stdout == "5\n" and r.timed_out is False and r.time_ms == 10.0


def test_execution_tle():
    def h(req):
        return httpx.Response(200, json={"status": {"id": 5, "description": "TLE"}})

    assert _provider(h).execute("python", "x", "", 1.0).timed_out is True


def test_execution_unreachable():
    def h(req):
        raise httpx.ConnectError("down", request=req)

    with pytest.raises(ExecutionUnavailableError):
        _provider(h).execute("python", "x", "", 1.0)


def test_execution_oversized_before_send():
    calls = {"n": 0}

    def h(req):
        calls["n"] += 1
        return httpx.Response(200, json={})

    with pytest.raises(SubmissionTooLargeError):
        _provider(h, max_bytes=10).execute("python", "x" * 100, "", 1.0)
    assert calls["n"] == 0


def test_execution_unsupported_language():
    def h(req):
        return httpx.Response(200, json={})

    with pytest.raises(UnsupportedLanguageError):
        _provider(h).execute("brainfuck", "+", "", 1.0)


# --- Piston provider (the free, keyless default) ---
def _piston(handler, max_bytes=64 * 1024):
    return PistonExecutionProvider(
        "https://emkc.org/api/v2/piston", "", max_bytes, transport=httpx.MockTransport(handler)
    )


def test_piston_success_and_no_auth_header():
    captured = {}

    def h(req):
        captured["auth"] = "Authorization" in req.headers
        return httpx.Response(200, json={"run": {"stdout": "5\n", "code": 0, "signal": None}})

    r = _piston(h).execute("python", "print(5)", "", 2.0)
    assert r.stdout == "5\n" and r.timed_out is False
    assert captured["auth"] is False  # public API is called with no key


def test_piston_maps_cpp_to_cplusplus():
    captured = {}

    def h(req):
        import json

        captured["language"] = json.loads(req.content)["language"]
        return httpx.Response(200, json={"run": {"stdout": "", "code": 0}})

    _piston(h).execute("cpp", "int main(){}", "", 1.0)
    assert captured["language"] == "c++"  # Piston rejects "cpp"


def test_piston_timeout_signal():
    def h(req):
        return httpx.Response(200, json={"run": {"stdout": "", "signal": "SIGKILL"}})

    assert _piston(h).execute("python", "while 1:pass", "", 1.0).timed_out is True


def test_piston_unreachable():
    def h(req):
        raise httpx.ConnectError("down", request=req)

    with pytest.raises(ExecutionUnavailableError):
        _piston(h).execute("python", "x", "", 1.0)


def test_piston_unsupported_language():
    def h(req):
        return httpx.Response(200, json={})

    with pytest.raises(UnsupportedLanguageError):
        _piston(h).execute("brainfuck", "+", "", 1.0)


# --- Paiza provider (the free, keyless DEFAULT) ---
def _paiza(handler, max_bytes=64 * 1024):
    return PaizaExecutionProvider(
        "https://api.paiza.io", "guest", max_bytes, transport=httpx.MockTransport(handler)
    )


def _paiza_handler(details, *, running_polls=0):
    """Mock the create -> poll -> details flow; records what was sent."""
    state = {"polls": 0, "sent": None}

    def h(req):
        if req.url.path.endswith("/runners/create"):
            state["sent"] = req.content.decode()
            return httpx.Response(200, json={"id": "sess-1", "status": "running"})
        if req.url.path.endswith("/runners/get_status"):
            state["polls"] += 1
            done = state["polls"] > running_polls
            return httpx.Response(200, json={"status": "completed" if done else "running"})
        return httpx.Response(200, json=details)

    return h, state


def test_paiza_success_uses_guest_key():
    h, state = _paiza_handler({"stdout": "42\n", "result": "success", "time": "0.01"})
    r = _paiza(h).execute("python", "print(42)", "", 2.0)
    assert r.stdout == "42\n" and r.timed_out is False and r.time_ms == 10.0
    assert "api_key=guest" in state["sent"]  # public runner, no account needed


def test_paiza_polls_until_completed():
    h, state = _paiza_handler({"stdout": "ok", "result": "success"}, running_polls=2)
    assert _paiza(h).execute("python", "x", "", 1.0).stdout == "ok"
    assert state["polls"] == 3  # two "running" then "completed"


def test_paiza_maps_language_and_passes_stdin():
    h, state = _paiza_handler({"stdout": "", "result": "success"})
    _paiza(h).execute("cpp", "int main(){}", "20 22", 1.0)
    assert "language=cpp" in state["sent"] and "20+22" in state["sent"]


def test_paiza_compile_error_surfaces_build_stderr():
    h, _ = _paiza_handler({"stdout": "", "result": "failure", "build_stderr": "syntax error"})
    r = _paiza(h).execute("cpp", "bad", "", 1.0)
    assert r.stderr == "syntax error" and r.status == "failure"


def test_paiza_timeout_result():
    h, _ = _paiza_handler({"stdout": "", "result": "timeout"})
    assert _paiza(h).execute("python", "while 1:pass", "", 1.0).timed_out is True


def test_paiza_unreachable():
    def h(req):
        raise httpx.ConnectError("down", request=req)

    with pytest.raises(ExecutionUnavailableError):
        _paiza(h).execute("python", "x", "", 1.0)


def test_paiza_missing_session_id_is_unavailable():
    def h(req):
        return httpx.Response(200, json={})  # no "id" back from create

    with pytest.raises(ExecutionUnavailableError):
        _paiza(h).execute("python", "x", "", 1.0)


def test_paiza_oversized_before_send():
    calls = {"n": 0}

    def h(req):
        calls["n"] += 1
        return httpx.Response(200, json={})

    with pytest.raises(SubmissionTooLargeError):
        _paiza(h, max_bytes=10).execute("python", "x" * 100, "", 1.0)
    assert calls["n"] == 0


def test_paiza_unsupported_language():
    def h(req):
        return httpx.Response(200, json={})

    with pytest.raises(UnsupportedLanguageError):
        _paiza(h).execute("brainfuck", "+", "", 1.0)


# --- Gemini structured-output compatibility (the "only interview worked" bug) ---
class _FreeFormSchema(BaseModel):
    """Mirrors McqItemSchema: `dict[str, str]` -> free-form object."""

    question: str
    options: dict[str, str]


class _ExplicitSchema(BaseModel):
    question: str
    answer: str


def test_free_form_dict_is_detected_as_incompatible():
    # Pydantic renders dict[str, str] as additionalProperties with no
    # `properties`; Gemini rejects that with 400 INVALID_ARGUMENT.
    assert _is_gemini_compatible(_ExplicitSchema.model_json_schema()) is True
    assert _is_gemini_compatible(_FreeFormSchema.model_json_schema()) is False


class _CapturingSDK:
    """Stands in for the google-genai client, recording the config it receives."""

    def __init__(self):
        self.config = None
        self.models = self

    def generate_content(self, *, model, contents, config):
        self.config = config
        return type("R", (), {"text": '{"question":"q","options":{"A":"x"}}'})()


def _client_with(sdk, monkeypatch):
    from apps.integrations.gemini.client import GeminiClient

    c = GeminiClient("key", "gemini-test", 5.0)
    monkeypatch.setattr(c, "_sdk", lambda: sdk)
    return c


def test_incompatible_schema_falls_back_to_json_mode(monkeypatch):
    sdk = _CapturingSDK()
    _client_with(sdk, monkeypatch).generate("p", response_schema=_FreeFormSchema)
    # JSON is still requested, but the rejected schema is NOT sent.
    assert sdk.config.response_mime_type == "application/json"
    assert sdk.config.response_schema is None


def test_compatible_schema_is_sent_natively(monkeypatch):
    sdk = _CapturingSDK()
    _client_with(sdk, monkeypatch).generate("p", response_schema=_ExplicitSchema)
    assert sdk.config.response_schema is _ExplicitSchema


def test_every_project_schema_survives_the_gate():
    # Guards against a schema that would crash the gate itself.
    from apps.interview.schemas import EvaluationSchema
    from apps.mcq.schemas import McqGenerationSchema
    from apps.oa.schemas import OAProblemSchema
    from apps.resume.schemas import ResumeAnalysisSchema

    for schema in (McqGenerationSchema, OAProblemSchema, ResumeAnalysisSchema, EvaluationSchema):
        assert isinstance(_is_gemini_compatible(schema.model_json_schema()), bool)
