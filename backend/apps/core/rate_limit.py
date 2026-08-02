"""Sliding-window rate limiter (in-memory), ported to Django middleware use.

Classifies requests by path into EXEC / AI / AUTH / STD and keys by
user → guest → IP. In-memory (resets on restart, per-worker) — the accepted
free-tier trade-off; Redis is the documented upgrade.
"""
from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque

from django.http import HttpRequest

_UNITS = {"second": 1, "minute": 60, "hour": 3600}


def parse_rate(rate: str) -> tuple[int, int]:
    count_str, unit = rate.split("/")
    unit = unit.strip().lower().rstrip("s")
    return int(count_str.strip()), _UNITS[unit]


def classify(path: str) -> str:
    if path.startswith("/api/v1/ai/oa/run") or path.startswith("/api/v1/ai/oa/submit"):
        return "EXEC"
    if path.startswith("/api/v1/ai/"):
        return "AI"
    if path.startswith("/api/v1/auth/"):
        return "AUTH"
    return "STD"


def identity(request: HttpRequest) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return "u:" + hashlib.sha256(auth[7:].encode()).hexdigest()[:16]
    guest = request.headers.get("X-Guest-Token")
    if guest:
        return "g:" + guest[:16]
    return "ip:" + (request.META.get("REMOTE_ADDR") or "unknown")


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_s: int) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        cutoff = now - window_s
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True
