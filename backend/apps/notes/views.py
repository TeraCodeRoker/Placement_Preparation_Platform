"""Notes endpoints — public listing + admin-gated upload/approve."""
from __future__ import annotations

import uuid

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.deps import require_admin
from apps.core.json_api import json_response, parse_body
from apps.core.pagination import limit_offset
from apps.notes.schemas import NoteCreate, NoteOut, NoteUpdate
from apps.notes.services import NotesService


@require_GET
def list_public(request: HttpRequest) -> HttpResponse:
    limit, offset = limit_offset(request, default_limit=50)
    notes = NotesService().list_public(limit, offset)
    return json_response([NoteOut.model_validate(n) for n in notes])


@require_http_methods(["GET", "POST"])
@require_admin
def admin_collection(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        req = parse_body(request, NoteCreate)
        with transaction.atomic():
            note = NotesService().create(request.current_user.id, req)
        return json_response(NoteOut.model_validate(note), status=201)
    limit, offset = limit_offset(request, default_limit=50)
    notes = NotesService().list_all(limit, offset)
    return json_response([NoteOut.model_validate(n) for n in notes])


@require_http_methods(["PATCH"])
@require_admin
def admin_update(request: HttpRequest, note_id: uuid.UUID) -> HttpResponse:
    req = parse_body(request, NoteUpdate)
    with transaction.atomic():
        note = NotesService().update(note_id, req)
    return json_response(NoteOut.model_validate(note))
