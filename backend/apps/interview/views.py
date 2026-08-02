"""Interview endpoints (plain Django views)."""
from __future__ import annotations

import uuid

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET, require_POST

from apps.core.deps import Identity, get_identity, require_user
from apps.core.exceptions import ForbiddenError
from apps.core.json_api import json_response, parse_body
from apps.core.pagination import limit_offset
from apps.integrations.gemini.service import get_gemini_service
from apps.interview.models import InterviewSession
from apps.interview.schemas import (
    AnswerRequest,
    CodeReviewRequest,
    CodeReviewResponse,
    InterviewHistoryItem,
    InterviewStartRequest,
)
from apps.interview.services import InterviewService


def _service() -> InterviewService:
    return InterviewService(get_gemini_service())


def _authorize(session: InterviewSession, identity: Identity) -> None:
    if session.user_id is not None and session.user_id != identity.user_id:
        raise ForbiddenError("This interview belongs to another account.")


@require_POST
def start(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, InterviewStartRequest)
    identity = get_identity(request)
    with transaction.atomic():
        resp = _service().start(identity, req.difficulty, req.num_subjective, req.num_dsa)
    return json_response(resp)


@require_POST
def answer(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, AnswerRequest)
    identity = get_identity(request)
    service = _service()
    session = service.get_session_or_404(req.session_id)
    _authorize(session, identity)
    with transaction.atomic():
        resp = service.answer(session, req.answer, req.idempotency_key)
    return json_response(resp)


@require_GET
def session_state(request: HttpRequest, session_id: uuid.UUID) -> HttpResponse:
    identity = get_identity(request)
    service = _service()
    session = service.get_session_or_404(session_id)
    _authorize(session, identity)
    return json_response(service.get_state(session))


@require_GET
@require_user
def history(request: HttpRequest) -> HttpResponse:
    limit, offset = limit_offset(request)
    sessions = InterviewSession.objects.filter(user_id=request.current_user.id).order_by(
        "-created_at"
    )[offset : offset + limit]
    items = [
        InterviewHistoryItem(
            session_id=s.id, status=s.status, total_questions=len(s.plan),
            created_at=s.created_at, completed_at=s.completed_at,
        )
        for s in sessions
    ]
    return json_response(items)


@require_POST
def code_review(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, CodeReviewRequest)
    review = _service().code_review(req.question, req.language, req.user_code)
    return json_response(CodeReviewResponse(review=review, language=req.language))
