"""Notes model (admin-uploaded, public when approved)."""
from __future__ import annotations

import uuid

from django.db import models


class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=128, default="")
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
