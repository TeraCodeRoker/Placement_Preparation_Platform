"""Resume endpoints (plain Django views; multipart for PDF uploads)."""
from __future__ import annotations

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET, require_POST

from apps.core.deps import get_identity, require_user
from apps.core.exceptions import BadRequestError
from apps.core.json_api import json_response, parse_body
from apps.core.pagination import limit_offset
from apps.integrations.gemini.service import get_gemini_service
from apps.resume.schemas import (
    AnalyzePdfResponse,
    AnalyzeRequest,
    AtsRequest,
    BulletRequest,
    PdfToJsonResponse,
    PlacementRequest,
    ResumeHistoryItem,
)
from apps.resume.services import ResumeService


def _service() -> ResumeService:
    return ResumeService(get_gemini_service())


@require_POST
def analyze(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, AnalyzeRequest)
    identity = get_identity(request)
    with transaction.atomic():
        result = _service().analyze(
            identity, req.resume_text, req.target_role, req.target_companies
        )
    return json_response(result)


@require_POST
def ats_score(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, AtsRequest)
    identity = get_identity(request)
    with transaction.atomic():
        result = _service().ats_score(identity, req.resume_text, req.job_description)
    return json_response(result)


@require_POST
def improve_bullet(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, BulletRequest)
    return json_response(_service().improve_bullet(req.bullet, req.context))


@require_POST
def placement_check(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, PlacementRequest)
    identity = get_identity(request)
    with transaction.atomic():
        result = _service().placement_check(identity, req.resume_text, req.dream_company)
    return json_response(result)


@require_POST
def pdf_to_json(request: HttpRequest) -> HttpResponse:
    file = request.FILES.get("file")
    if file is None:
        raise BadRequestError("No file uploaded.")
    text, structured = _service().pdf_to_json(file.name, file.read())
    return json_response(
        PdfToJsonResponse(filename=file.name, resume_text=text, structured=structured)
    )


@require_POST
def analyze_pdf(request: HttpRequest) -> HttpResponse:
    file = request.FILES.get("file")
    if file is None:
        raise BadRequestError("No file uploaded.")
    target_role = request.POST.get("target_role", "")
    raw_companies = request.POST.get("target_companies", "")
    companies = [c.strip() for c in raw_companies.split(",") if c.strip()]
    identity = get_identity(request)
    with transaction.atomic():
        text, analysis = _service().analyze_pdf(
            identity, file.name, file.read(), target_role, companies
        )
    return json_response(
        AnalyzePdfResponse(resume_text=text, target_role=target_role, analysis=analysis)
    )


@require_GET
@require_user
def history(request: HttpRequest) -> HttpResponse:
    limit, offset = limit_offset(request)
    rows = _service().history(request.current_user.id, limit, offset)
    items = [
        ResumeHistoryItem(
            id=r.id, target_role=r.target_role, kind=r.kind, verdict=r.verdict,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return json_response(items)
