# ADR-019 — Backend framework: plain Django (overhaul from FastAPI)

**Status:** Accepted · **Supersedes the FastAPI implementation** · Relates to §5

## Context
Django is the preferred backend framework. The system was rebuilt from FastAPI to
**plain Django** (no DRF, no Django Ninja), replacing the FastAPI backend entirely
while **preserving the exact `/api/v1` HTTP contract** so the React frontend is
unchanged.

## Decision & mapping
| FastAPI | → Plain Django |
|---|---|
| `app/` + routers | Django project `prepstack/` + per-context **apps** (`accounts`, `interview`, `mcq`, `resume`, `oa`, `notes`, `core`, `integrations`) |
| Pydantic schemas | **Kept** (framework-neutral validation — §10.2 requires it), used in views via a `json_api` helper. Not DRF serializers. |
| SQLAlchemy models + repository classes | **Django ORM models + querysets/managers** (the idiomatic Django data layer) |
| Alembic | **Django migrations** |
| `Depends` guards | **view decorators** (`@require_user`/`@require_admin`) + `get_identity()` |
| `CORSMiddleware` / slowapi / request-id | **Django middleware** (`django-cors-headers` + a ported sliding-window limiter + request-id + error-envelope) |
| uvicorn (ASGI) | **Gunicorn (WSGI)** |
| httpx.AsyncClient | Django `TestClient` in tests |

## Async → sync (the key translation)
FastAPI is async-first; every external call used `await` (`client.aio`, async
httpx). **Django's concurrency is worker/thread-based** (Gunicorn workers), so the
idiomatic translation is **synchronous I/O**: the sync google-genai client
(`client.models.generate_content` with an HTTP timeout) and sync `httpx.Client`
for Judge0. There is no event loop to block, so "no blocking call inside
`async def`" (§10.1) doesn't apply; correctness under concurrency comes from the
worker model. Reliability is preserved: retry + jittered backoff + circuit
breaker (now `time.sleep`-based).

**Alternatives rejected:** DRF (heavier, and its async story is weak — but a
strong default; not chosen because the user asked for plain Django); Django Ninja
(near-1:1 with FastAPI, async + Pydantic) — not chosen for the same reason.

## What's preserved
- The full `/api/v1` contract (paths, request/response shapes, cookies, error
  envelope) → **frontend untouched** (`client.js`/`endpoints.js` unchanged).
- All features, the shared Gemini layer + prompts + error taxonomy, the execution
  Strategy, upload hardening, guest/claim, idempotency, honest OA scoring +
  degraded mode, CORS lockdown, per-identity rate limiting, injection fencing,
  and the 5 failure-mode tests.

## Consequences
- **DATABASE_URL uses the Django scheme** (`postgres://`, not
  `postgresql+asyncpg://`); settings normalize the async scheme for safety.
- Repository-pattern ADR (008) is realized as Django ORM access from services (no
  separate repository classes — un-idiomatic in Django).
- mypy is scoped to the framework-neutral layers (`integrations`, core
  exceptions/security); Django views/models are thin and would need django-stubs.
