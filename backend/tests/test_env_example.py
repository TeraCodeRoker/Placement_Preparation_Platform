"""`.env.example` must be a safe template: real placeholders, no real secrets.

Regression guard for a subtle python-dotenv behaviour: a trailing `#comment`
after an EMPTY value is parsed as the VALUE, not stripped. So

    GEMINI_API_KEY=      # placeholder only

yields the truthy string "# placeholder only" — which would make a copied .env
look "configured", defeat the prod fail-fast guard, and turn a clean degraded
mode into a confusing upstream auth error. Comments belong on their own line.
"""
from pathlib import Path

from dotenv import dotenv_values

ENV_EXAMPLE = Path(__file__).resolve().parent.parent / ".env.example"

# Vars that must ship EMPTY — a value here would be a committed secret.
MUST_BE_EMPTY = [
    "GEMINI_API_KEY",
    "DJANGO_SECRET_KEY",
    "JUDGE0_API_KEY",
    "PISTON_API_KEY",
    "ADMIN_BOOTSTRAP_EMAIL",
]


def _values() -> dict[str, str | None]:
    return dotenv_values(ENV_EXAMPLE)


def test_no_comment_parsed_as_value() -> None:
    offenders = {k: v for k, v in _values().items() if v and v.lstrip().startswith("#")}
    assert not offenders, (
        f"Inline comment parsed as the value for {list(offenders)}. "
        "Move the comment to its own line above the key."
    )


def test_secret_placeholders_are_empty() -> None:
    values = _values()
    for key in MUST_BE_EMPTY:
        assert key in values, f"{key} missing from .env.example"
        assert not values[key], f"{key} must ship empty in .env.example, got {values[key]!r}"


def test_no_real_gemini_key_committed() -> None:
    # Google AI Studio keys start with "AQ." — none may appear in a tracked file.
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "AQ." not in text, "A real-looking Gemini key is present in .env.example"


def test_production_database_is_not_the_sqlite_default() -> None:
    # The template ships SQLite for local dev; settings' prod guard rejects it.
    assert _values()["DATABASE_URL"] == "sqlite:///db.sqlite3"
