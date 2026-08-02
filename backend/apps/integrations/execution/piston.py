"""Piston execution provider — the free, keyless default strategy (sync).

Uses the public Piston API (``https://emkc.org/api/v2/piston``) which requires no
account and no API key, so the OA compiler runs real code at zero cost. A
self-hosted Piston (or a keyed gateway) works too via ``PISTON_URL`` /
``PISTON_API_KEY``. Judge0 remains an alternative strategy (ADR-005/ADR-020).
"""
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

# Frontend/OA language token -> (Piston language name, runtime version on emkc.org).
# Piston is picky about names ("c++", not "cpp") so we normalize here.
_LANGUAGES = {
    "python": ("python", "3.10.0"),
    "python3": ("python", "3.10.0"),
    "java": ("java", "15.0.2"),
    "cpp": ("c++", "10.2.0"),
    "c++": ("c++", "10.2.0"),
    "c": ("c", "10.2.0"),
    "javascript": ("javascript", "18.15.0"),
    "js": ("javascript", "18.15.0"),
    "node": ("javascript", "18.15.0"),
}


class PistonExecutionProvider(CodeExecutionProvider):
    name = "piston"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        max_source_bytes: int,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._max_source_bytes = max_source_bytes
        self._transport = transport  # injectable for tests (httpx.MockTransport)

    def execute(
        self, language: str, source_code: str, stdin: str, timeout_s: float
    ) -> ExecutionResult:
        enforce_source_size(source_code, self._max_source_bytes)
        mapped = _LANGUAGES.get(language.lower())
        if mapped is None:
            raise UnsupportedLanguageError(f"Language '{language}' is not supported.")
        piston_language, version = mapped

        payload = {
            "language": piston_language,
            "version": version,
            "files": [{"content": source_code}],
            "stdin": stdin,
            "run_timeout": int(timeout_s * 1000),
        }
        headers = {"Content-Type": "application/json"}
        if self._api_key:  # only for keyed/self-hosted gateways; public API needs none
            headers["Authorization"] = self._api_key
        try:
            with httpx.Client(timeout=timeout_s + 10, transport=self._transport) as client:
                response = client.post(f"{self._base_url}/execute", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ExecutionUnavailableError() from exc

        run = data.get("run") or {}
        signal = run.get("signal")
        return ExecutionResult(
            stdout=run.get("stdout") or "",
            stderr=run.get("stderr") or "",
            time_ms=None,
            timed_out=signal in ("SIGKILL", "SIGXCPU"),  # Piston kills on run_timeout
            status=str(run.get("code", "")),
        )
