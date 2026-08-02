"""Django settings — all config from environment (12-factor).

Plain Django (no DRF): a stateless JWT API, so the session/auth/CSRF middleware
stack is intentionally omitted (we do our own JWT auth + double-submit CSRF).
Fails fast in prod if real secrets are missing (see ``_assert_production_ready``).
"""
from __future__ import annotations

import os
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_bool(key: str, default: bool) -> bool:
    return os.environ.get(key, str(default)).strip().lower() in ("1", "true", "yes", "on")


# --- App environment ---
APP_ENV = _env("APP_ENV", "local")
DEBUG = _env_bool("DEBUG", APP_ENV != "prod")

_DEV_SECRET = "dev-only-insecure-change-me"
JWT_SECRET = _env("JWT_SECRET", _DEV_SECRET)
SECRET_KEY = _env("DJANGO_SECRET_KEY") or JWT_SECRET  # Django's own key
ALLOWED_HOSTS = ["*"]  # same-origin proxy in prod; tighten if exposed directly

# --- Application config (read via django.conf.settings) ---
GEMINI_API_KEY = _env("GEMINI_API_KEY")
GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_TIMEOUT_S = float(_env("GEMINI_TIMEOUT_S", "30"))

JWT_ALGORITHM = "HS256"
JWT_ACCESS_TTL_MIN = int(_env("JWT_ACCESS_TTL_MIN", "15"))
JWT_REFRESH_TTL_DAYS = int(_env("JWT_REFRESH_TTL_DAYS", "7"))
ADMIN_BOOTSTRAP_EMAIL = _env("ADMIN_BOOTSTRAP_EMAIL")
GUEST_TTL_DAYS = int(_env("GUEST_TTL_DAYS", "7"))
MCQ_CACHE_TTL_HOURS = int(_env("MCQ_CACHE_TTL_HOURS", "24"))

# Default: Paiza.io's public runner — free, keyless (api_key=guest). See ADR-020.
EXECUTION_PROVIDER = _env("EXECUTION_PROVIDER", "paiza")
PAIZA_URL = _env("PAIZA_URL", "https://api.paiza.io")
PAIZA_API_KEY = _env("PAIZA_API_KEY", "guest")
# Alternatives (self-hosted or keyed): piston, judge0.
PISTON_URL = _env("PISTON_URL", "https://emkc.org/api/v2/piston")
PISTON_API_KEY = _env("PISTON_API_KEY")
JUDGE0_URL = _env("JUDGE0_URL", "https://judge0-ce.p.rapidapi.com")
JUDGE0_HOST = _env("JUDGE0_HOST", "judge0-ce.p.rapidapi.com")
JUDGE0_API_KEY = _env("JUDGE0_API_KEY")
EXECUTION_TIMEOUT_S = float(_env("EXECUTION_TIMEOUT_S", "10"))
EXECUTION_MAX_SOURCE_BYTES = int(_env("EXECUTION_MAX_SOURCE_BYTES", str(64 * 1024)))
OA_WALL_CLOCK_S = float(_env("OA_WALL_CLOCK_S", "25"))

RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)
RATE_LIMITS = {
    "AI": _env("RATE_LIMIT_AI", "20/minute"),
    "EXEC": _env("RATE_LIMIT_EXEC", "10/minute"),
    "AUTH": _env("RATE_LIMIT_AUTH", "10/minute"),
    "STD": _env("RATE_LIMIT_STD", "60/minute"),
}

# --- CORS (§9.1: explicit origins, never "*") ---
ALLOWED_ORIGINS = [
    o.strip() for o in _env("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]
CORS_ALLOWED_ORIGINS = ALLOWED_ORIGINS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (*default_headers, "x-csrf-token", "x-guest-token", "x-request-id")

# --- Django plumbing ---
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "corsheaders",
    "apps.core",
    "apps.accounts",
    "apps.integrations",
    "apps.interview",
    "apps.mcq",
    "apps.resume",
    "apps.oa",
    "apps.notes",
]

# Stateless JWT API: only our own middleware (CORS + request-id + rate-limit +
# error-envelope). No session/auth/CSRF middleware by design.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "apps.core.middleware.RequestContextMiddleware",
    "apps.core.middleware.RateLimitMiddleware",
    "apps.core.middleware.ErrorEnvelopeMiddleware",
]

ROOT_URLCONF = "prepstack.urls"
WSGI_APPLICATION = "prepstack.wsgi.application"
APPEND_SLASH = False  # exact API paths; never redirect a POST

# Normalize async URL schemes (FastAPI-era or Neon +asyncpg) to Django-compatible.
_raw_db_url = os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
_raw_db_url = _raw_db_url.replace("postgresql+asyncpg://", "postgres://").replace(
    "sqlite+aiosqlite://", "sqlite://"
)
DATABASES = {"default": dj_database_url.parse(_raw_db_url, conn_max_age=600)}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
STATIC_URL = "static/"

# Upload caps (defense-in-depth for resume PDFs).
DATA_UPLOAD_MAX_MEMORY_SIZE = 11 * 1024 * 1024  # slightly above the 10 MB PDF cap


def _assert_production_ready() -> None:
    if APP_ENV != "prod":
        return
    problems = []
    if JWT_SECRET == _DEV_SECRET or len(JWT_SECRET) < 16:
        problems.append("JWT_SECRET (strong, non-default, >=16 chars)")
    if not GEMINI_API_KEY:
        problems.append("GEMINI_API_KEY")
    if str(DATABASES["default"].get("ENGINE", "")).endswith("sqlite3"):
        problems.append("DATABASE_URL (must be Postgres in production, not SQLite)")
    if problems:
        raise RuntimeError(
            "Invalid production configuration — missing/insecure: " + ", ".join(problems)
        )


_assert_production_ready()
