"""Resume analysis history model (stores PII → ADR-010)."""
from __future__ import annotations

import uuid

from django.db import models


class ResumeAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.CASCADE,
        related_name="resume_analyses",
    )
    guest = models.ForeignKey(
        "accounts.GuestSession", null=True, blank=True, on_delete=models.CASCADE,
        related_name="resume_analyses",
    )
    target_role = models.CharField(max_length=128, default="")
    kind = models.CharField(max_length=32)  # analyze | ats | placement
    scores = models.JSONField()
    verdict = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resume_analyses"
