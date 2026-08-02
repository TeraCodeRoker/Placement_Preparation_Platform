"""OA endpoints (plain Django views)."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET, require_POST

from apps.core.deps import get_identity
from apps.core.json_api import json_response, parse_body
from apps.integrations.execution.factory import get_execution_provider
from apps.integrations.gemini.service import get_gemini_service
from apps.oa.schemas import OAProblemRequest, OARunRequest, OASubmitRequest
from apps.oa.services import OAService


def _service() -> OAService:
    return OAService(
        get_gemini_service(),
        get_execution_provider(),
        settings.EXECUTION_MAX_SOURCE_BYTES,
        settings.EXECUTION_TIMEOUT_S,
        settings.OA_WALL_CLOCK_S,
    )


@require_POST
def problem(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, OAProblemRequest)
    with transaction.atomic():
        result = _service().create_problem(req.step, req.topic, req.languages, req.num_hidden)
    return json_response(result)


@require_POST
def run(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, OARunRequest)
    return json_response(_service().run(req.problem_id, req.language, req.source_code))


@require_POST
def submit(request: HttpRequest) -> HttpResponse:
    req = parse_body(request, OASubmitRequest)
    identity = get_identity(request)
    with transaction.atomic():
        result = _service().submit(identity, req.problem_id, req.language, req.source_code)
    return json_response(result)


@require_GET
def submission(request: HttpRequest, submission_id: uuid.UUID) -> HttpResponse:
    identity = get_identity(request)
    return json_response(_service().get_submission_out(submission_id, identity))
