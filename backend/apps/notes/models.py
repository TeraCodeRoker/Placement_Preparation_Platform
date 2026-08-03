"""Notes model (admin-uploaded, public when approved)."""
from __future__ import annotations

import uuid

from django.db import models


class Note(models.Model):
    """A study resource.

    The API exposes *what* a note is (subject, unit, kind, size) and never *where*
    it physically lives — ``content_or_url`` is an opaque pointer, so moving files
    from the static site to object storage later is a data migration, not an API
    change.
    """

    KIND_CHOICES = [
        ("pdf", "PDF"),
        ("slides", "Slides"),
        ("doc", "Document"),
        ("syllabus", "Syllabus"),
        ("image", "Image"),
        ("link", "Link"),
        ("text", "Text"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=128, default="")
    # Chapter/module grouping within a subject, e.g. "Unit 1" or "Overview".
    unit = models.CharField(max_length=128, default="", blank=True)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default="link")
    # 0 when unknown (e.g. an external link); lets the UI warn before a big download.
    size_bytes = models.PositiveBigIntegerField(default=0)
    sort_order = models.IntegerField(default=0)
    content_or_url = models.TextField()
    # Keep the note if the uploading admin's account is deleted.
    uploaded_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="notes",
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notes"
        ordering = ["subject", "sort_order", "title"]
        indexes = [models.Index(fields=["approved", "subject", "sort_order"])]
        constraints = [
            # The importer is re-runnable; a subject+unit+title is one resource.
            models.UniqueConstraint(
                fields=["subject", "unit", "title"], name="uniq_note_subject_unit_title"
            )
        ]
