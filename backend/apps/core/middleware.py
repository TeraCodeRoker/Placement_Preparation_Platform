"""Django middleware: request-id/logging, rate limiting, and error envelope."""
from __future__ import annotations

import time
import uuid
from collections.abc import Callable

import structlog
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from apps.core.exceptions import AppError
from apps.core.rate_limit import SlidingWindowLimiter, classify, identity, parse_rate

_logger = structlog.get_logger("request")
_error_logger = structlog.get_logger("error")

GetResponse = Callable[[HttpRequest], HttpResponse]


def _envelope(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


class RequestContextMiddleware:
    def __init__(self, get_response: GetResponse) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id, method=request.method, path=request.path
        )
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        _logger.info("request_completed", status=response.status_code, duration_ms=duration_ms)
        response["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware:
    def __init__(self, get_response: GetResponse) -> None:
        self.get_response = get_response
        self._enabled = settings.RATE_LIMIT_ENABLED
        self._rates = {cls: parse_rate(r) for cls, r in settings.RATE_LIMITS.items()}
        self._limiter = SlidingWindowLimiter()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self._enabled:
            return self.get_response(request)
        rate_class = classify(request.path)
        limit, window = self._rates.get(rate_class, self._rates["STD"])
        key = f"{rate_class}:{identity(request)}"
        if not self._limiter.allow(key, limit, window):
            resp = JsonResponse(
                _envelope("rate_limit_exceeded", "Too many requests. Please retry shortly."),
                status=429,
            )
            resp["Retry-After"] = str(window)
            return resp
        return self.get_response(request)


class ErrorEnvelopeMiddleware:
    """Maps raised AppErrors to the envelope; unhandled errors → generic 500."""

    def __init__(self, get_response: GetResponse) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(self, request: HttpRequest, exc: Exception) -> HttpResponse | None:
        if isinstance(exc, AppError):
            headers = {}
            if exc.code == "rate_limit_exceeded":
                headers["Retry-After"] = "60"
            resp = JsonResponse(
                _envelope(exc.code, exc.message, exc.details), status=exc.status_code
            )
            for key, value in headers.items():
                resp[key] = value
            return resp
        _error_logger.error("unhandled_exception", exc_info=exc)
        return JsonResponse(
            _envelope("internal_error", "An unexpected error occurred."), status=500
        )
