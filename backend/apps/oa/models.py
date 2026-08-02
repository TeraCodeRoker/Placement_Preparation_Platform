"""OA problem + submission models."""
from __future__ import annotations

import uuid

from django.db import models


class OAProblem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step = models.CharField(max_length=128)
    topic = models.CharField(max_length=255)
    statement = models.TextField()
    starter_code = models.JSONField()
    visible_tests = models.JSONField()
    hidden_tests = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "oa_problems"


class OASubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    problem = models.ForeignKey(
        OAProblem, on_delete=models.CASCADE, related_name="submissions"
    )
    user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.CASCADE,
        related_name="oa_submissions",
    )
    guest = models.ForeignKey(
        "accounts.GuestSession", null=True, blank=True, on_delete=models.CASCADE,
        related_name="oa_submissions",
    )
    language = models.CharField(max_length=32)
    source_code = models.TextField()
    test_results = models.JSONField()
    pass_count = models.IntegerField()
    total_count = models.IntegerField()
    ai_review = models.JSONField(null=True, blank=True)
    final_score = models.IntegerField()
    mode = models.CharField(max_length=24, default="graded")  # graded | ai_review_only
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "oa_submissions"
