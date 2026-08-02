"""Demo seed is idempotent + password-gated for users."""
import pytest

from apps.accounts.models import User
from apps.core.seed import seed
from apps.mcq.models import McqSet
from apps.notes.models import Note
from apps.oa.models import OAProblem

pytestmark = pytest.mark.django_db


def test_seed_creates_then_idempotent() -> None:
    first = seed(password="demo-password-123")
    assert first == {"users": 2, "notes": 2, "mcq_sets": 1, "oa_problems": 1}

    second = seed(password="demo-password-123")
    assert second == {"users": 0, "notes": 0, "mcq_sets": 0, "oa_problems": 0}

    assert User.objects.count() == 2
    assert Note.objects.count() == 2
    assert McqSet.objects.count() == 1
    assert OAProblem.objects.count() == 1


def test_seed_without_password_skips_users() -> None:
    created = seed(password=None)
    assert created["users"] == 0
    assert created["notes"] == 2
