"""The notes library importer: idempotent, prunable, curriculum-ordered."""
import json

import pytest
from django.core.management import call_command
from django.test import Client

from apps.notes.models import Note

pytestmark = pytest.mark.django_db

ENTRY = {
    "subject": "Operating Systems",
    "unit": "Unit 1",
    "title": "Scheduling",
    "kind": "pdf",
    "url": "/notes/operating-systems/unit-1/scheduling.pdf",
    "size_bytes": 1048576,
    "sort_order": 3,
}


def _manifest(tmp_path, entries):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return str(path)


def test_import_is_idempotent(tmp_path):
    manifest = _manifest(tmp_path, [ENTRY])
    call_command("import_notes", manifest=manifest)
    call_command("import_notes", manifest=manifest)

    assert Note.objects.count() == 1  # re-running updates, never duplicates
    note = Note.objects.get()
    assert (note.subject, note.unit, note.kind) == ("Operating Systems", "Unit 1", "pdf")
    assert note.size_bytes == 1048576
    assert note.approved is True


def test_import_can_stage_notes_for_review(tmp_path):
    call_command("import_notes", manifest=_manifest(tmp_path, [ENTRY]), unapproved=True)
    assert Note.objects.get().approved is False
    # Hidden notes must not leak into the public listing.
    assert Client().get("/api/v1/notes").json() == []


def test_reimport_updates_changed_metadata(tmp_path):
    call_command("import_notes", manifest=_manifest(tmp_path, [ENTRY]))
    changed = {**ENTRY, "size_bytes": 42, "url": "/notes/moved.pdf"}
    call_command("import_notes", manifest=_manifest(tmp_path, [changed]))

    note = Note.objects.get()
    assert note.size_bytes == 42
    assert note.content_or_url == "/notes/moved.pdf"


def test_prune_removes_notes_dropped_from_the_manifest(tmp_path):
    second = {**ENTRY, "title": "Deadlocks", "url": "/notes/os/deadlocks.pdf"}
    call_command("import_notes", manifest=_manifest(tmp_path, [ENTRY, second]))
    assert Note.objects.count() == 2

    call_command("import_notes", manifest=_manifest(tmp_path, [ENTRY]), prune=True)
    assert [n.title for n in Note.objects.all()] == ["Scheduling"]


def test_prune_spares_manually_added_notes(tmp_path):
    # An admin-uploaded external link is not part of the imported set.
    Note.objects.create(
        title="Handwritten", subject="OS", content_or_url="https://example.com/x", approved=True
    )
    call_command("import_notes", manifest=_manifest(tmp_path, [ENTRY]), prune=True)
    assert Note.objects.filter(title="Handwritten").exists()


def test_public_listing_exposes_browsing_metadata(tmp_path):
    call_command("import_notes", manifest=_manifest(tmp_path, [ENTRY]))
    row = Client().get("/api/v1/notes").json()[0]
    # The client needs these to build the subject -> unit tree and warn on size.
    for field in ("subject", "unit", "kind", "size_bytes", "content_or_url"):
        assert field in row, f"{field} missing from the public contract"


def test_listing_is_in_curriculum_order_not_upload_order(tmp_path):
    entries = [
        {**ENTRY, "title": "Later", "unit": "Unit 2", "sort_order": 9},
        {**ENTRY, "title": "Earlier", "unit": "Unit 1", "sort_order": 1},
    ]
    call_command("import_notes", manifest=_manifest(tmp_path, entries))
    titles = [n["title"] for n in Client().get("/api/v1/notes").json()]
    assert titles == ["Earlier", "Later"]


def test_missing_manifest_fails_loudly(tmp_path):
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("import_notes", manifest=str(tmp_path / "nope.json"))


def test_shipped_manifest_matches_the_static_files():
    """The committed manifest is the deploy contract — keep it honest."""
    from pathlib import Path

    from apps.notes.management.commands.import_notes import DEFAULT_MANIFEST

    entries = json.loads(Path(DEFAULT_MANIFEST).read_text(encoding="utf-8"))
    assert entries, "manifest is empty"

    public = Path(DEFAULT_MANIFEST).parents[4] / "frontend" / "public"
    missing = [e["url"] for e in entries if not (public / e["url"].lstrip("/")).exists()]
    assert not missing, f"manifest references {len(missing)} missing files, e.g. {missing[:3]}"

    assert not any(" " in e["url"] for e in entries), "URLs must be slugified"
    assert not any("ebook" in e["url"].lower() for e in entries), "eBooks must not ship"
