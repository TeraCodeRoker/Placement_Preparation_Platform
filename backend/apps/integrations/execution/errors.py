"""Execution failure taxonomy."""
from __future__ import annotations

from apps.core.exceptions import AppError


class ExecutionError(AppError):
    status_code = 502
    code = "execution_error"
    message = "Code execution failed."


class ExecutionUnavailableError(ExecutionError):
    status_code = 503
    code = "execution_unavailable"
    message = "Code execution service is temporarily unavailable."


class UnsupportedLanguageError(ExecutionError):
    status_code = 400
    code = "unsupported_language"
    message = "This language is not supported by the execution provider."


class SubmissionTooLargeError(ExecutionError):
    status_code = 413
    code = "submission_too_large"
    message = "Submitted code exceeds the size limit."
