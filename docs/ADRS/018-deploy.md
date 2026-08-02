# ADR-018 — Deployment (Render free tier)

**Status:** Accepted · **Relates to:** §3, §9.3

## Decision
Deploy from a committed `render.yaml` Blueprint: one **web service** (backend,
native Python buildpack) + one **static site** (frontend, global CDN).

- **Buildpack, not Docker (ADR-012):** faster builds against Render's shared free
  build-minute budget, smaller/managed image, lower cold-start; no system
  dependency requires a custom image (`pdfplumber` is pure-pip).
- **Migrations at build:** `alembic upgrade head` runs in the build command
  (Render free tier has no `preDeployCommand`); env vars are available at build.
- **Same-origin via static-site rewrite:** the static site proxies `/api/*` and
  `/health` to the backend, so the SPA is same-origin and the `SameSite=Lax`
  refresh cookie works (ADR-004). Cross-site fallback documented.

## "Why this survives the free tier"
- **Cold start (15-min idle spin-down):** one web service → one cold start; the
  `/health` probe drives a "waking up" banner so it doesn't look broken.
- **512 MB / shared CPU:** single FastAPI process; code execution delegated to
  Judge0 (never in-process); Monaco lazy-loaded off the main bundle.
- **Ephemeral disk:** no durable data on disk — Postgres (Neon) holds everything;
  SQLite only for tests.
- **Request timeout:** every Gemini/exec call has a timeout < Render's, bounded
  retries, and a circuit breaker to avoid pile-ups.

## Rollback
Render keeps the previous successful deploy live on a failed build/deploy — a bad
push never takes the site down. Auto-deploy on merge to `main`.

## Observability
`/health` (liveness) + `/health/detailed` (DB round-trip + provider-config
status) + structured JSON logs with a request-id — enough to answer "how would I
know if this broke" on a free tier without a Prometheus stack.
