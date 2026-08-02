"""Judge0 CE execution provider (default primary, sync)."""
from __future__ import annotations

import httpx

from apps.integrations.execution.base import (
    CodeExecutionProvider,
    ExecutionResult,
    enforce_source_size,
)
from apps.integrations.execution.errors import (
    ExecutionUnavailableError,
    UnsupportedLanguageError,
)

_LANGUAGE_IDS = {
    "python": 71,
    "python3": 71,
    "java": 62,
    "cpp": 54,
    "c++": 54,
    "c": 50,
    "javascript": 63,
    "js": 63,
}
_STATUS_TIME_LIMIT_EXCEEDED = 5


class Judge0ExecutionProvider(CodeExecutionProvider):
    name = "judge0"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        host: str,
        max_source_bytes: int,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._host = host
        self._max_source_bytes = max_source_bytes
        self._transport = transport  # injectable for tests (httpx.MockTransport)

    def execute(
        self, language: str, source_code: str, stdin: str, timeout_s: float
    ) -> ExecutionResult:
        enforce_source_size(source_code, self._max_source_bytes)
        language_id = _LANGUAGE_IDS.get(language.lower())
        if language_id is None:
            raise UnsupportedLanguageError(f"Language '{language}' is not supported.")

        payload = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
            "cpu_time_limit": timeout_s,
        }
        headers = {
            "X-RapidAPI-Key": self._api_key,
            "X-RapidAPI-Host": self._host,
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/submissions?base64_encoded=false&wait=true"
        try:
            with httpx.Client(timeout=timeout_s + 10, transport=self._transport) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ExecutionUnavailableError() from exc

        status = data.get("status") or {}
        raw_time = data.get("time")
        return ExecutionResult(
            stdout=data.get("stdout") or "",
            stderr=(data.get("stderr") or data.get("compile_output") or ""),
            time_ms=(float(raw_time) * 1000) if raw_time else None,
            timed_out=status.get("id") == _STATUS_TIME_LIMIT_EXCEEDED,
            status=status.get("description") or "",
        )
