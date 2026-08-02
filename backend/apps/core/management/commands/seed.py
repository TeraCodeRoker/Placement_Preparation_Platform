"""`python manage.py seed` — idempotent demo data (set SEED_PASSWORD for users)."""
from __future__ import annotations

import os
from typing import Any

from django.core.management.base import BaseCommand

from apps.core.seed import seed


class Command(BaseCommand):
    help = "Seed demo data idempotently (approved notes, an MCQ set, an OA problem)."

    def handle(self, *args: Any, **options: Any) -> None:
        created = seed(password=os.environ.get("SEED_PASSWORD"))
        self.stdout.write(self.style.SUCCESS(f"Seed complete: {created}"))
