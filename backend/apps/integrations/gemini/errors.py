"""Gemini failure taxonomy (§10.6)."""
from __future__ import annotations

from apps.core.exceptions import AppError


class GeminiError(AppError):
    status_code = 502
    code = "gemini_error"
    message = "The AI service could not process this request."


class GeminiUnavailableError(GeminiError):
    status_code = 503
    code = "gemini_unavailable"
    message = "AI service is temporarily unavailable, please retry."


class GeminiRateLimitedError(GeminiError):
    """Quota / rate limit (HTTP 429, RESOURCE_EXHAUSTED).

    Distinct from ``GeminiUnavailableError`` because retrying immediately makes it
    worse — it spends more of the quota that is already exhausted.
    """

    status_code = 429
    code = "gemini_rate_limited"
    message = (
        "AI request quota reached for now. Free-tier limits refill after a short "
        "wait — please try again in a minute."
    )


class GeminiEmptyResponseError(GeminiError):
    status_code = 502
    code = "gemini_empty_response"
    message = (
        "The AI returned an empty response (it may have been blocked). "
        "Please rephrase and retry."
    )


class GeminiMalformedResponseError(GeminiError):
    status_code = 502
    code = "gemini_malformed_response"
    message = "The AI response could not be processed. Please retry."


class GeminiSchemaViolationError(GeminiError):
    status_code = 502
    code = "gemini_schema_violation"
    message = "The AI response did not match the expected format. Please retry."
