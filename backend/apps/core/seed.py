"""Idempotent demo-data seed.

Seeds public demo content always; demo user + admin only when a password is
supplied (never hardcode credentials). Safe to run repeatedly.
"""
from __future__ import annotations

from django.conf import settings

from apps.accounts.models import User
from apps.core.security import hash_password
from apps.mcq.models import McqQuestion, McqSet
from apps.notes.models import Note
from apps.oa.models import OAProblem


def seed(password: str | None = None) -> dict[str, int]:
    created = {"users": 0, "notes": 0, "mcq_sets": 0, "oa_problems": 0}

    if password:
        admin_email = settings.ADMIN_BOOTSTRAP_EMAIL or "admin@prepstack.local"
        for email, role in [(admin_email, "admin"), ("demo@prepstack.local", "user")]:
            if not User.objects.filter(email=email).exists():
                User.objects.create(
                    email=email, hashed_password=hash_password(password), role=role
                )
                created["users"] += 1

    if not Note.objects.exists():
        Note.objects.create(
            title="OS — Scheduling cheatsheet", subject="Operating Systems",
            content_or_url="FCFS, SJF, RR, priority; convoy effect; RR quantum trade-offs.",
            approved=True,
        )
        Note.objects.create(
            title="DBMS — Normal forms", subject="DBMS",
            content_or_url="1NF to BCNF with examples; lossless-join decomposition.",
            approved=True,
        )
        created["notes"] += 2

    if not McqSet.objects.exists():
        mcq_set = McqSet.objects.create(
            topic="Operating Systems", subtopic="", count=1, difficulty="medium",
            cache_key="seed|operating systems||1|medium",
        )
        McqQuestion.objects.create(
            set=mcq_set,
            question="Which scheduling algorithm can cause starvation?",
            options={"A": "Round Robin", "B": "FCFS", "C": "Priority (non-aging)", "D": "SJF"},
            correct_answer="C",
            explanation="Low-priority processes may never run without aging.",
        )
        created["mcq_sets"] += 1

    if not OAProblem.objects.exists():
        OAProblem.objects.create(
            step="Step 3 - Arrays", topic="Sum of two integers",
            statement="Read two integers from stdin and print their sum.",
            starter_code={"python": "a, b = map(int, input().split())\nprint(a + b)"},
            visible_tests=[{"stdin": "2 3", "expected_output": "5"}],
            hidden_tests=[{"stdin": "10 20", "expected_output": "30"}],
        )
        created["oa_problems"] += 1

    return created
