"""MCQ endpoints (plain Django views)."""
from __future__ import annotations

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET, require_POST

from apps.core.deps import get_identity, require_user
from apps.core.json_api import json_response, parse_body
from apps.core.pagination import limit_offset
from apps.integrations.gemini.service import get_gemini_service
from apps.mcq.models import McqAttempt
from apps.mcq.schemas import (
    AttemptRequest,
    DailyChallengeRequest,
    McqGenerateRequest,
    McqHistoryItem,
)
from apps.mcq.services import McqService


def _service() -> McqService:
    return McqService(get_gemini_service(), settings.MCQ_CACHE_TTL_HOURS)


@require_POST
def generate(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, McqGenerateRequest)
    with transaction.atomic():
        result = _service().generate(req.topic, req.subtopic, req.count, req.difficulty)
    return json_response(result)


@require_POST
def daily_challenge(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, DailyChallengeRequest)
    with transaction.atomic():
        result = _service().daily_challenge(req.topic)
    return json_response(result)


@require_POST
def attempt(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, AttemptRequest)
    identity = get_identity(request)
    with transaction.atomic():
        result = _service().record_attempt(identity, req)
    return json_response(result)


@require_GET
@require_user
def history(request: HttpRequest) -> HttpResponse:
    limit, offset = limit_offset(request)
    attempts = McqAttempt.objects.filter(user_id=request.current_user.id).order_by(
        "-created_at"
    )[offset : offset + limit]
    items = [
        McqHistoryItem(
            id=a.id, subject=a.subject, difficulty=a.difficulty, correct=a.correct,
            total=a.total, percent=round((a.correct / a.total) * 100) if a.total else 0,
            created_at=a.created_at,
        )
        for a in attempts
    ]
    return json_response(items)
