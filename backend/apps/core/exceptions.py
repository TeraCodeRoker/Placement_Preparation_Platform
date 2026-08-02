"""Internal exception hierarchy (framework-neutral).

Views/services raise these; ``ErrorEnvelopeMiddleware`` maps them to the
consistent envelope ``{"error": {code, message, details}}`` so raw exception
strings never reach clients. Provider-specific errors (Gemini, execution)
subclass ``AppError`` in their integration modules.
"""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"
    message = "Bad request."


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Resource not found."


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"
    message = "Invalid input."


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "payload_too_large"
    message = "The uploaded file is too large."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "Resource conflict."


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    message = "Authentication required."


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    message = "You do not have access to this resource."


class RateLimitExceededError(AppError):
    status_code = 429
    code = "rate_limit_exceeded"
    message = "Too many requests. Please retry shortly."
