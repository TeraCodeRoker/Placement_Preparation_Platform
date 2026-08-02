"""MCQ set / question / attempt models (generation cache + history)."""
from __future__ import annotations

import uuid

from django.db import models


class McqSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=128)
    subtopic = models.CharField(max_length=128, default="")
    count = models.IntegerField()
    difficulty = models.CharField(max_length=16)
    cache_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mcq_sets"


class McqQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    set = models.ForeignKey(McqSet, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=8)
    explanation = models.TextField(default="")

    class Meta:
        db_table = "mcq_questions"


class McqAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.CASCADE,
        related_name="mcq_attempts",
    )
    guest = models.ForeignKey(
        "accounts.GuestSession", null=True, blank=True, on_delete=models.CASCADE,
        related_name="mcq_attempts",
    )
    # Keep attempt history even if the cached set is later evicted.
    set = models.ForeignKey(
        McqSet, null=True, blank=True, on_delete=models.SET_NULL, related_name="attempts"
    )
    subject = models.CharField(max_length=128, default="")
    difficulty = models.CharField(max_length=16, default="")
    correct = models.IntegerField()
    total = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mcq_attempts"
