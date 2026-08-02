"""Paiza.io execution provider — the free, keyless default strategy (sync).

Paiza's public runner accepts ``api_key=guest``: no account, no card, no payment.
It is an async (create → poll → details) API, wrapped here behind the same
synchronous ``CodeExecutionProvider`` seam as every other strategy (ADR-020).

Chosen after the public Piston API went whitelist-only (2026-02-15) and Judge0 CE
moved to paid RapidAPI tiers — both remain selectable via ``EXECUTION_PROVIDER``
for anyone who self-hosts or holds a key.
"""
from __future__ import annotations

import time

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

# Frontend/OA language token -> Paiza language id.
_LANGUAGES = {
    "python": "python3",
    "python3": "python3",
    "java": "java",
    "cpp": "cpp",
    "c++": "cpp",
    "c": "c",
    "javascript": "javascript",
    "js": "javascript",
    "node": "javascript",
}
_POLL_INTERVAL_S = 0.6


class PaizaExecutionProvider(CodeExecutionProvider):
    name = "paiza"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        max_source_bytes: int,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key or "guest"  # public runner accepts the literal "guest"
        self._max_source_bytes = max_source_bytes
        self._transport = transport  # injectable for tests (httpx.MockTransport)

    def execute(
        self, language: str, source_code: str, stdin: str, timeout_s: float
    ) -> ExecutionResult:
        enforce_source_size(source_code, self._max_source_bytes)
        paiza_language = _LANGUAGES.get(language.lower())
        if paiza_language is None:
            raise UnsupportedLanguageError(f"Language '{language}' is not supported.")

        # Budget the whole create+poll cycle so a stuck job can't pin a worker.
        deadline = time.monotonic() + timeout_s + 15
        try:
            with httpx.Client(timeout=timeout_s + 10, transport=self._transport) as client:
                created = client.post(
                    f"{self._base_url}/runners/create",
                    data={
                        "source_code": source_code,
                        "language": paiza_language,
                        "input": stdin,
                        "longpoll": "true",
                        "api_key": self._api_key,
                    },
                )
                created.raise_for_status()
                session_id = (created.json() or {}).get("id")
                if not session_id:
                    raise ExecutionUnavailableError()

                params = {"id": session_id, "api_key": self._api_key}
                while True:
                    status_resp = client.get(f"{self._base_url}/runners/get_status", params=params)
                    status_resp.raise_for_status()
                    if (status_resp.json() or {}).get("status") == "completed":
                        break
                    if time.monotonic() > deadline:
                        return ExecutionResult(timed_out=True, status="time limit exceeded")
                    time.sleep(_POLL_INTERVAL_S)

                details = client.get(f"{self._base_url}/runners/get_details", params=params)
                details.raise_for_status()
                data = details.json() or {}
        except httpx.HTTPError as exc:
            raise ExecutionUnavailableError() from exc

        result = data.get("result") or ""
        raw_time = data.get("time")
        return ExecutionResult(
            stdout=data.get("stdout") or "",
            # Compile errors surface in build_stderr; runtime errors in stderr.
            stderr=(data.get("stderr") or data.get("build_stderr") or ""),
            time_ms=(float(raw_time) * 1000) if raw_time else None,
            timed_out=result == "timeout",
            status=result,
        )
