"""Notes orchestration (sync + Django ORM)."""
from __future__ import annotations

import uuid

from apps.core.exceptions import NotFoundError
from apps.notes.models import Note
from apps.notes.schemas import NoteCreate, NoteUpdate


class NotesService:
    def create(self, uploaded_by: uuid.UUID, data: NoteCreate) -> Note:
        return Note.objects.create(
            title=data.title, subject=data.subject, unit=data.unit, kind=data.kind,
            size_bytes=data.size_bytes, sort_order=data.sort_order,
            content_or_url=data.content_or_url,
            approved=data.approved, uploaded_by_id=uploaded_by,
        )

    def list_all(self, limit: int, offset: int) -> list[Note]:
        return list(Note.objects.order_by("-created_at")[offset : offset + limit])

    def list_public(self, limit: int, offset: int) -> list[Note]:
        # Curriculum order (subject -> unit -> title), not upload order: the
        # library is browsed as a syllabus, not as a feed.
        return list(
            Note.objects.filter(approved=True).order_by("subject", "sort_order", "title")[
                offset : offset + limit
            ]
        )

    def update(self, note_id: uuid.UUID, data: NoteUpdate) -> Note:
        note = Note.objects.filter(id=note_id).first()
        if note is None:
            raise NotFoundError("Note not found.")
        if data.title is not None:
            note.title = data.title
        if data.subject is not None:
            note.subject = data.subject
        if data.unit is not None:
            note.unit = data.unit
        if data.kind is not None:
            note.kind = data.kind
        if data.sort_order is not None:
            note.sort_order = data.sort_order
        if data.content_or_url is not None:
            note.content_or_url = data.content_or_url
        if data.approved is not None:
            note.approved = data.approved
        note.save()
        return note
