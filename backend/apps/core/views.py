"""Health checks."""
from __future__ import annotations

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

VERSION = "0.1.0"


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "healthy"})


@require_GET
def health_detailed(request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "up"
    except Exception:
        db_status = "down"

    # Report readiness, not raw key presence: the default provider (Paiza) and a
    # self-hosted Piston need no secret; only Judge0 requires a RapidAPI key.
    if settings.EXECUTION_PROVIDER == "judge0":
        execution_ready = bool(settings.JUDGE0_API_KEY)
    else:
        execution_ready = True
    return JsonResponse(
        {
            "status": "healthy" if db_status == "up" else "degraded",
            "version": VERSION,
            "db": db_status,
            "gemini": "configured" if settings.GEMINI_API_KEY else "unconfigured",
            "execution_provider": settings.EXECUTION_PROVIDER,
            "execution": "ready" if execution_ready else "unconfigured",
        }
    )
