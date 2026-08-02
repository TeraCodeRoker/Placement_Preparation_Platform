"""Interview session + per-question result models."""
from __future__ import annotations

import uuid

from django.db import models


class InterviewSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Exactly one owner (application-enforced): a user or a guest.
    user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.CASCADE,
        related_name="interview_sessions",
    )
    guest = models.ForeignKey(
        "accounts.GuestSession", null=True, blank=True, on_delete=models.CASCADE,
        related_name="interview_sessions",
    )
    plan = models.JSONField()
    status = models.CharField(max_length=16, default="active")
    current_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "interview_sessions"


class InterviewResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        InterviewSession, on_delete=models.CASCADE, related_name="results"
    )
    question_number = models.IntegerField()
    question_type = models.CharField(max_length=16)
    subject = models.CharField(max_length=128)
    topic = models.CharField(max_length=255)
    question = models.TextField()
    answer = models.TextField()
    score = models.IntegerField()
    feedback = models.TextField(default="")
    correct_answer = models.TextField(default="")
    answer_idempotency_key = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "interview_results"
        constraints = [
            models.UniqueConstraint(
                fields=["session", "answer_idempotency_key"],
                name="uq_result_session_idempotency",
            )
        ]
