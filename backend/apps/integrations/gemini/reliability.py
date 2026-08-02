"""Circuit breaker for the Gemini dependency (§10.4). In-memory, per-process."""
from __future__ import annotations

import time


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 5, reset_timeout_s: float = 30.0) -> None:
        self._fail_threshold = fail_threshold
        self._reset_timeout_s = reset_timeout_s
        self._failures = 0
        self._opened_at: float | None = None

    def allow(self) -> bool:
        if self._opened_at is None:
            return True
        return time.monotonic() - self._opened_at >= self._reset_timeout_s

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._fail_threshold:
            self._opened_at = time.monotonic()
