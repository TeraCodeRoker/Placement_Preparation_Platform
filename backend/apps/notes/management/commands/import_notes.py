"""Seed the notes library from the committed manifest.

The manifest (``apps/notes/fixtures/notes_manifest.json``) is the contract between
the static files shipped in ``frontend/public/notes/`` and the database rows that
describe them. Keeping it in the repo means a fresh deploy can rebuild the library
with one command and no upload step.

Idempotent: re-running updates existing rows in place (matched on
subject + unit + title) instead of duplicating them.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.notes.models import Note

_APPS_DIR = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = _APPS_DIR / "notes" / "fixtures" / "notes_manifest.json"


class Command(BaseCommand):
    help = "Import/refresh study notes from the manifest (idempotent)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
        parser.add_argument(
            "--unapproved",
            action="store_true",
            help="Import hidden, for review in the admin panel first.",
        )
        parser.add_argument(
            "--prune",
            action="store_true",
            help="Delete imported notes that are no longer in the manifest.",
        )

    def handle(self, *args: Any, **opts: Any) -> None:
        path = Path(opts["manifest"])
        if not path.exists():
            raise CommandError(f"Manifest not found: {path}")

        entries = json.loads(path.read_text(encoding="utf-8"))
        approved = not opts["unapproved"]
        created = updated = 0
        seen: set[tuple[str, str, str]] = set()

        with transaction.atomic():
            for e in entries:
                key = (e["subject"], e["unit"], e["title"])
                seen.add(key)
                _, was_created = Note.objects.update_or_create(
                    subject=e["subject"],
                    unit=e["unit"],
                    title=e["title"],
                    defaults={
                        "kind": e["kind"],
                        "size_bytes": e["size_bytes"],
                        "sort_order": e["sort_order"],
                        "content_or_url": e["url"],
                        "approved": approved,
                    },
                )
                created += was_created
                updated += not was_created

            pruned = 0
            if opts["prune"]:
                for note in Note.objects.filter(content_or_url__startswith="/notes/"):
                    if (note.subject, note.unit, note.title) not in seen:
                        note.delete()
                        pruned += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"notes imported: {created} created, {updated} updated"
                + (f", {pruned} pruned" if opts["prune"] else "")
                + ("" if approved else " (hidden pending approval)")
            )
        )
