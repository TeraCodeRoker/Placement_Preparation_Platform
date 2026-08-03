"""GeminiService (sync) — the single entry point every AI feature uses.

Wraps the client with jittered retry, a circuit breaker, the error taxonomy,
defensive JSON parsing, and Pydantic validation. Feature services depend on this
(never on the SDK) and mock it in tests.
"""
from __future__ import annotations

import random
import time
from typing import Protocol, TypeVar

import structlog
from pydantic import BaseModel, ValidationError

from apps.integrations.gemini.adapters import extract_json
from apps.integrations.gemini.client import get_gemini_client
from apps.integrations.gemini.errors import (
    GeminiEmptyResponseError,
    GeminiError,
    GeminiSchemaViolationError,
    GeminiUnavailableError,
)
from apps.integrations.gemini.reliability import CircuitBreaker

SchemaT = TypeVar("SchemaT", bound=BaseModel)

_logger = structlog.get_logger("gemini")


class SupportsGenerate(Protocol):
    def generate(self, prompt: str, *, response_schema: type[BaseModel] | None = None) -> str: ...


class GeminiService:
    def __init__(
        self,
        client: SupportsGenerate,
        *,
        max_retries: int = 2,
        backoff_base_s: float = 0.3,
        jitter_s: float = 0.2,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        self._client = client
        self._max_retries = max_retries
        self._backoff_base_s = backoff_base_s
        self._jitter_s = jitter_s
        self._breaker = breaker or CircuitBreaker()

    def _generate_raw(self, prompt: str, response_schema: type[BaseModel] | None) -> str:
        last_error: GeminiUnavailableError | None = None
        for attempt in range(self._max_retries + 1):
            if not self._breaker.allow():
                raise GeminiUnavailableError("AI service temporarily unavailable (circuit open).")
            try:
                raw = self._client.generate(prompt, response_schema=response_schema)
            except GeminiError:
                raise  # already classified (e.g. missing key)
            except Exception as exc:  # timeout / network / provider = transient
                self._breaker.record_failure()
                _logger.warning(
                    "gemini_transient_failure",
                    attempt=attempt + 1,
                    of=self._max_retries + 1,
                    error_type=type(exc).__name__,
                    detail=str(exc)[:300],
                )
                last_error = GeminiUnavailableError()
                if attempt < self._max_retries:
                    time.sleep(
                        self._backoff_base_s * (2**attempt) + random.uniform(0, self._jitter_s)
                    )
                    continue
                raise last_error from None
            else:
                self._breaker.record_success()
                return raw
        raise last_error or GeminiUnavailableError()

    def generate_json(self, prompt: str, schema: type[SchemaT]) -> SchemaT:
        raw = self._generate_raw(prompt, schema)
        if not raw.strip():
            raise GeminiEmptyResponseError()
        data = extract_json(raw)
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise GeminiSchemaViolationError() from exc

    def generate_text(self, prompt: str) -> str:
        raw = self._generate_raw(prompt, None)
        if not raw.strip():
            raise GeminiEmptyResponseError()
        return raw.strip()


_service_singleton: GeminiService | None = None


def get_gemini_service() -> GeminiService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = GeminiService(get_gemini_client())
    return _service_singleton
