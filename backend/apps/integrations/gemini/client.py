"""The one place that talks to the google-genai SDK (sync).

Django's concurrency is worker/thread-based (Gunicorn), so we use the SYNC SDK
(``client.models.generate_content``) rather than the async path — the idiomatic
translation of the FastAPI async I/O (ADR-019). Lazy client init so the app boots
without a real key; an HTTP timeout guards against hung calls (§10.4).
"""
from __future__ import annotations

from typing import Any

import structlog
from django.conf import settings
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from apps.integrations.gemini.errors import (
    GeminiRateLimitedError,
    GeminiUnavailableError,
)

_logger = structlog.get_logger("gemini")


def _is_gemini_compatible(schema: dict[str, Any]) -> bool:
    """Can this JSON Schema be sent as Gemini's ``response_schema``?

    Gemini's structured output accepts only a subset of JSON Schema: every object
    must declare explicit ``properties``. Pydantic renders ``dict[str, X]`` as a
    free-form object (``additionalProperties`` and no ``properties``), which the
    API rejects with 400 INVALID_ARGUMENT — failing the whole request.
    """

    def walk(node: Any) -> bool:
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" not in node:
                return False
            return all(walk(v) for v in node.values())
        if isinstance(node, list):
            return all(walk(v) for v in node)
        return True

    return walk(schema)


class GeminiClient:
    def __init__(self, api_key: str, model: str, timeout_s: float = 30.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_ms = int(timeout_s * 1000)
        self._sdk_client: genai.Client | None = None

    def _sdk(self) -> genai.Client:
        if self._sdk_client is None:
            if not self._api_key:
                raise GeminiUnavailableError("GEMINI_API_KEY is not configured.")
            self._sdk_client = genai.Client(
                api_key=self._api_key,
                http_options=types.HttpOptions(timeout=self._timeout_ms),
            )
        return self._sdk_client

    def generate(self, prompt: str, *, response_schema: type[BaseModel] | None = None) -> str:
        config: types.GenerateContentConfig | None = None
        if response_schema is not None:
            if _is_gemini_compatible(response_schema.model_json_schema()):
                config = types.GenerateContentConfig(
                    response_mime_type="application/json", response_schema=response_schema
                )
            else:
                # A free-form object (dict[str, X]) would make the API reject the
                # request outright. Ask for JSON without the schema — the prompt
                # already specifies the shape, and GeminiService still validates
                # the parsed result against this same Pydantic model.
                _logger.info("gemini_schema_fallback", schema=response_schema.__name__)
                config = types.GenerateContentConfig(response_mime_type="application/json")
        try:
            response = self._sdk().models.generate_content(
                model=self._model, contents=prompt, config=config
            )
        except genai_errors.APIError as exc:
            # The SDK's own taxonomy is the only place the real cause is visible.
            # Log it, or every upstream failure reaches the user as an
            # indistinguishable "temporarily unavailable".
            _logger.warning(
                "gemini_api_error",
                http_code=exc.code,
                status=exc.status,
                detail=str(exc.message)[:300],
                model=self._model,
            )
            if exc.code == 429 or exc.status == "RESOURCE_EXHAUSTED":
                raise GeminiRateLimitedError() from exc
            raise
        return response.text or ""


_client_singleton: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
            timeout_s=settings.GEMINI_TIMEOUT_S,
        )
    return _client_singleton
