"""The one place that talks to the google-genai SDK (sync).

Django's concurrency is worker/thread-based (Gunicorn), so we use the SYNC SDK
(``client.models.generate_content``) rather than the async path — the idiomatic
translation of the FastAPI async I/O (ADR-019). Lazy client init so the app boots
without a real key; an HTTP timeout guards against hung calls (§10.4).
"""
from __future__ import annotations

from django.conf import settings
from google import genai
from google.genai import types
from pydantic import BaseModel

from apps.integrations.gemini.errors import GeminiUnavailableError


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
            config = types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=response_schema
            )
        response = self._sdk().models.generate_content(
            model=self._model, contents=prompt, config=config
        )
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
