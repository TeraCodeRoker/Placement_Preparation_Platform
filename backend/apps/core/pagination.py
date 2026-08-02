"""limit/offset query parsing (ADR-009)."""
from __future__ import annotations

from django.http import HttpRequest


def limit_offset(
    request: HttpRequest, *, default_limit: int = 20, max_limit: int = 100
) -> tuple[int, int]:
    def _int(name: str, default: int) -> int:
        try:
            return int(request.GET.get(name, default))
        except (TypeError, ValueError):
            return default

    limit = max(1, min(max_limit, _int("limit", default_limit)))
    offset = max(0, _int("offset", 0))
    return limit, offset
